from django.shortcuts import render
from django.conf import settings
from general.views import get_sister

from .models import Office, OfficeInterest

def index(request):
  return render(request, 'elections/index.html', {})

def ois_submission(request):
  # Determine whether OIS is open
  try:
    ois_open = settings.OIS_OPEN
  except:
    ois_open = False
  if not ois_open:
    return render(request, 'elections/ois_submission.html', {'ois_closed': True})

  # Get initial data
  offices = Office.objects.all()
  sister = get_sister(request)
  context = {
    'offices': offices
  }

  # If just rendering the page, see if the user has
  # already completed OIS
  if request.method == 'GET':
    submitted = True
    for office in offices:
      # Check if there's an entry for each office
      try:
        office_interest = OfficeInterest.objects.get(sister=sister, office=office)
      except:
        submitted = False
        break
    context['submitted'] = submitted

  # If user submitted the form, see if every field
  # is filled out.
  elif request.method == 'POST':
    # Save the user's result and
    # make sure they selected something for every office.
    for office in offices:
      # Make sure user selected something for every office
      try:
        interest = request.POST[str(office.id)]
        office_interest = OfficeInterest(sister=sister, office=office, interest=interest)
        office_interest.save()
      except:
        # User didn't select something for this office
        context['error'] = True
        return render(request, 'elections/ois_submission.html', context)

    # If got through for loop, sister has completed OIS
    context['submitted'] = True

  return render(request, 'elections/ois_submission.html', context)

def ois_results(request):
  # TODO: Sort by position then by interest
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

