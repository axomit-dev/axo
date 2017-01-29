from django.shortcuts import render
from django.conf import settings
from general.views import get_sister

from .models import Office, OfficeInterest

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

  # Get initial data
  offices = Office.objects.all()
  sister = get_sister(request)
  context = {
    'offices': offices
  }

  # If they pressed submit, store that data
  if request.method == 'POST':
    for office in offices:
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

