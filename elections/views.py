from django.shortcuts import render
from django.conf import settings
from general.views import get_sister
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import ElectionSettings, Office, OfficeInterest, Loi, LoiForm
from general.models import Sister

##########################
##### HELPER METHODS #####
##########################

# Returns true if the sister is eligible to run / vote
# for the given office.
def is_eligible(sister, office):
  if office.eligible_class == Office.ALL_CLASSES:
    return True
  else:
    # TODO: Better way to do this?
    if office.eligible_class == Office.FRESHMAN:
      class_year = get_election_settings().senior_class_year + 3
    elif office.eligible_class == Office.SOPHOMORE:
      class_year = get_election_settings().senior_class_year + 2
    elif office.eligible_class == Office.JUNIOR:
      class_year = get_election_settings().senior_class_year + 1
    else: # office.eligible_class == Office.SENIOR:
      class_year = get_election_settings().senior_class_year

    return sister.class_year == class_year

# Returns the current election settings.
def get_election_settings():
  # There should always be exactly one ElectionSettings instance.
  return ElectionSettings.objects.all().first()

# Returns true if it's an exec election and false otherwise
def is_exec_election():
  return get_election_settings().exec_election

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

  # Determine whether sister is eligible to run for each office
  offices = Office.objects.filter(is_exec=is_exec_election())
  sister = get_sister(request)
  for office in offices:
    office.is_eligible = is_eligible(sister, office)
    office.save()

  # Set what should be displayed on the page  
  context = {
    'offices': offices,
    'exec_election': is_exec_election(),
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
        # Exception if they didn't select interest level
        # for this office
        context['error'] = True
        return render(request, 'elections/ois_submission.html', context)

    # If got through the whole for loop, they've submitted it
    context['submitted'] = True
    # TODO: return HttpResponseRedirect since we successfully dealt
    # with POST data.

  return render(request, 'elections/ois_submission.html', context)

@login_required
def ois_results(request):
  results = OfficeInterest.objects.all()
  return render(request, 'elections/ois_results.html', {'results': results})

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
    print("in if")
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
    print("in else")
    # Otherwise, just show them the form
    form = LoiForm(is_exec_election())

  print("form:")
  print(LoiForm(is_exec_election()))

  context['form'] = form

  return render(request, 'elections/loi_submission.html', context)

@login_required
def loi_results(request):
  results = Loi.objects.all()
  return render(request, 'elections/loi_results.html', {'results': results})

@login_required
def slating_submission(request):
  # Determine whether slating submission is open

  # TODO: Abstract away the 'figuring out if something is open' stuff
  # ^ will also need for the 'viewing results' part
  # Could possibly let VP CRS say when she wants everything to open + close
  # and automatically change things.....?


  if not get_election_settings().slating_open:
    return render(request, 'elections/slating_submission.html', {'slating_closed': True})


  # TODO: Add logic for handling POST

  lois = Loi.objects.all()

  return render(request, 'elections/slating_submission.html', {'lois': lois})

# TODO: Make this superuser only
@login_required
def slating_results(request):
  return render(request, 'elections/slating_results.html', {})

@login_required
def voting_submission(request):
  return render(request, 'elections/voting_submission.html', {})

# TODO: Make this superuser only
@login_required
def voting_results(request):
  return render(request, 'elections/voting_results.html', {})

