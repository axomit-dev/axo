from django.shortcuts import render
from django.conf import settings
from general.views import get_sister
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import ElectionSettings, Office, OfficeInterest, Loi, LoiForm, Slate, is_eligible, get_election_settings
from general.models import Sister

# TODO: Automatically stop someone from slating/voting
# if they haven't done OIS, slated, etc.

# TODO: Don't let an alum, disaffiliated person, etc.
# do any elections things.

##########################
##### HELPER METHODS #####
##########################

# Returns true if it's an exec election and false otherwise
def is_exec_election():
  return get_election_settings().exec_election

# Returns a list of positions that the sister has not submitted
# an OIS for.
# all_offices: Is a list of all the offices that a sister needs to
# submit an OIS for, and is augmented with the 'is_eligible' field
# which specifies whether the sister is eligible to run for that
# position.
def get_ois_empty_offices(sister, all_offices):
  empty_offices = []
  for office in all_offices:
    # If they're not eligible for the office, move on
    if not office.is_eligible:
      continue

    # See if they've already submitted for this position
    try:
      office_interest = OfficeInterest.objects.get(sister=sister, office=office)
    except:
      # If not, add it to the list
      empty_offices.append(office)

  return empty_offices


#################
##### VIEWS #####
#################

# TODO: Bold which menu items are 'active'

# TODO: Add description of what 'LOIs', 'Slating', voting are

@login_required
def index(request):
  return render(request, 'elections/index.html', {})

@login_required
def ois_submission(request):
  # TODO: Display whether they've submitted it already

  if not get_election_settings().ois_open:
    return render(request, 'elections/ois_submission.html', {'ois_closed': True})


  # Used to determine if a sister has started her OIS or not
  num_eligible_offices = 0;

  # Determine whether sister is eligible to run for each office
  offices = Office.objects.filter(is_exec=is_exec_election())
  sister = get_sister(request)
  for office in offices:
    office.is_eligible = is_eligible(sister, office)
    office.save()
    if is_eligible(sister, office):
      num_eligible_offices += 1

  # Set what should be displayed on the page  
  context = {
    'offices': offices,
    'num_eligible_offices': num_eligible_offices, 
    'exec_election': is_exec_election(),
    'empty_offices': get_ois_empty_offices(sister, offices)
  }

  # If they pressed submit, store that data
  if request.method == 'POST':

    for office in offices:
      # If they're not eligible for the office, move on
      if not office.is_eligible:
        continue

      # See if they've already submitted for this position
      try:
        office_interest = OfficeInterest.objects.get(sister=sister, office=office)
      except:
        # If not, make a new instance
        office_interest = OfficeInterest(sister=sister, office=office)
      
      # Save the level of interest given
      try:
        interest = int(request.POST[str(office.id)])
        office_interest.interest = interest
        office_interest.save()
      except:
        pass

    # If got through the whole for loop, they've submitted it
    context['submitted'] = True
    # Reset what 'empty_offices' is because it's likely changed
    context['empty_offices'] = get_ois_empty_offices(sister, offices)
    # TODO: return HttpResponseRedirect since we successfully dealt
    # with POST data.

  return render(request, 'elections/ois_submission.html', context)

@login_required
def ois_results(request):
  if not get_election_settings().ois_results_open:
    return render(request, 'elections/ois_results.html', {'ois_results_closed': True})

  # Display sisters who haven't submitted OIS 
  # TODO: If they've only submitted half their OIS,
  #   are they allowed to slate/vote? 
  sister_who_did_ois = set()
  for ois in OfficeInterest.objects.all():
    # This sister did cast a slate
    sister_who_did_ois.add(ois.sister)

  sisters_no_ois = Sister.objects \
    .exclude(id__in=[s.id for s in sister_who_did_ois]) \
    .exclude(status=Sister.ALUM) \
    .exclude(status=Sister.ABROAD) \
    .exclude(status=Sister.DEAFFILIATED)

  context = {
    'results': OfficeInterest.objects.all(),
    'sisters_no_ois': sisters_no_ois
  }

  return render(request, 'elections/ois_results.html', context)

@login_required
def loi_submission(request):
  # TODO: Show if they've already submitted an LOI before
  # TODO: Restrict selecting multiple sisters if it's a 1-person position?
  # TODO: Require that they have to select themselves and/or auto-select themselves?

  if not get_election_settings().loi_open:
    return render(request, 'elections/loi_submission.html', {'loi_closed': True})

  context = {}

  # If they pressed submit, process and store that data
  if request.method == 'POST':
    form = LoiForm(is_exec_election(), request.POST)
    if form.is_valid():
      # Delete any pre-existing LOIs
      try:
        old_loi = Loi.objects.get(sisters=form.cleaned_data['sisters'], office=form.cleaned_data['office'])
        old_loi.delete()
      except:
        pass

      form.save()
      context['success'] = True


  else:
    # Otherwise, just show them the form
    form = LoiForm(is_exec_election())

  context['form'] = form

  return render(request, 'elections/loi_submission.html', context)

@login_required
def loi_results(request):
  if not get_election_settings().loi_results_open:
    return render(request, 'elections/loi_results.html', {'loi_results_closed': True})

  results = Loi.objects.all()
  return render(request, 'elections/loi_results.html', {'results': results})

# TODO: Not associate a user with their slate?
# Unsure how 'private' a slate has to be
@login_required
def slating_submission(request):
  # Determine whether slating submission is open
  if not get_election_settings().slating_open:
    return render(request, 'elections/slating_submission.html', {'slating_closed': True})

  # TODO: Have better metric of when a sister has
  # submitted her slate
  
  # Determine if sister has already submitted her slate
  sister = get_sister(request)
  sister_slate = Slate.objects.filter(sister=sister)
  if sister_slate:
    return render(request, 'elections/slating_submission.html', {'has_slated': True})

  # Submit their slate
  if request.method == 'POST':
    offices = Office.objects.filter(is_exec=is_exec_election())

    for office in offices:
      vote_1 = None
      vote_2 = None

      # Get first vote
      try:
        vote_1_id = request.POST[str(office.id)+"_vote_1"]
        vote_1 = Loi.objects.get(id=vote_1_id)
      except:
        # Voted 'Abstain'
        pass

      # Get second vote
      try:
        vote_2_id = request.POST[str(office.id)+"_vote_2"]
         # Can't vote for the same candidate twice
        if vote_2_id != vote_1_id: 
          vote_2 = Loi.objects.get(id=vote_2_id)
      except:
        # Voted 'Abstain'
        pass

      slate = Slate(sister=sister, office=office, vote_1=vote_1, vote_2=vote_2)
      slate.save()

    # Slate has been submitted
    return render(request, 'elections/slating_submission.html', {'has_slated': True})

  # Not submitting slate, so just render the page
  # With LOIs for the current type of election
  lois = Loi.objects.filter(office__is_exec=is_exec_election())

  # TODO: What do to if there's no LOIs for a position in the election?
  return render(request, 'elections/slating_submission.html', {'lois': lois})

@user_passes_test(lambda u: u.is_superuser)
def slating_results(request):
  slating_results = {}

  # Calcuate number of votes for each candidate for each office
  offices = Office.objects.filter(is_exec=is_exec_election())
  for office in offices:
    # All candidates running for that office
    lois_for_office = Loi.objects.filter(office=office)

    # Stores how many votes each candidate received
    vote_counts = {}
    for loi in lois_for_office:
      vote_counts[loi.names_of_sisters()] = 0

    # Calculate the vote counts
    slates_for_office = Slate.objects.filter(office=office)
    for slate in slates_for_office:
      if slate.vote_1:
        vote_counts[slate.vote_1.names_of_sisters()] += 1
      if slate.vote_2:
        vote_counts[slate.vote_2.names_of_sisters()] += 1

    slating_results[office] = vote_counts

  # Display sisters who haven't slated  
  sister_who_slated = []
  for slate in Slate.objects.all():
    # This sister did cast a slate
    sister_who_slated.append(slate.sister)

  sisters_no_slate = Sister.objects \
    .exclude(id__in=[s.id for s in sister_who_slated]) \
    .exclude(status=Sister.ALUM) \
    .exclude(status=Sister.ABROAD) \
    .exclude(status=Sister.DEAFFILIATED)

  context = {
    'slating_results': slating_results,
    'sisters_no_slate': sisters_no_slate,
  }

  return render(request, 'elections/slating_results.html', context)

@login_required
def voting_submission(request):
  return render(request, 'elections/voting_submission.html', {})

@user_passes_test(lambda u: u.is_superuser)
def voting_results(request):
  return render(request, 'elections/voting_results.html', {})

