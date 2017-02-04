from django.shortcuts import render
from django.conf import settings
from general.views import get_sister
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Office, OfficeInterest

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
      class_year = settings.SENIOR_CLASS_YEAR + 3
    elif office.eligible_class == Office.SOPHOMORE:
      class_year = settings.SENIOR_CLASS_YEAR + 2
    elif office.eligible_class == Office.JUNIOR:
      class_year = settings.SENIOR_CLASS_YEAR + 1
    else: # office.eligible_class == Office.SENIOR:
      class_year = settings.SENIOR_CLASS_YEAR

    return sister.class_year == class_year

@login_required
def index(request):
  return render(request, 'elections/index.html', {})

@login_required
def ois_submission(request):
  # TODO: Display whether they've submitted it already?


  # Determine whether OIS is open
  try:
    ois_open = settings.OIS_OPEN
  except:
    ois_open = False
  if not ois_open:
    return render(request, 'elections/ois_submission.html', {'ois_closed': True})

  # Determine whether it's an exec or non-exec election
  try:
    exec_election = settings.EXEC_ELECTION
  except:
    exec_election = False

  # Determine whether sister is eligible to run for each office
  offices = Office.objects.filter(is_exec=exec_election)
  sister = get_sister(request)
  for office in offices:
    office.is_eligible = is_eligible(sister, office)
    office.save()
  context = {
    'offices': offices,
    'exec_election': exec_election,
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

def loi_submission(request):
  return render(request, 'elections/loi_submission.html', {})

def loi_results(request):
  return render(request, 'elections/loi_results.html', {})

def slating_submission(request):
  return render(request, 'elections/slating_submission.html', {})

def slating_results(request):
  return render(request, 'elections/slating_results.html', {})

def voting_submission(request):
  return render(request, 'elections/voting_submission.html', {})

def voting_results(request):
  return render(request, 'elections/voting_results.html', {})

