from django.shortcuts import render
from django.conf import settings
from general.views import get_sister

from .models import Office

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

  offices = Office.objects.all()
  context = {
    'offices': offices
  }

  # See if user tried submitting the form
  if request.method == 'POST':
    # User clicked submit button
    sister = get_sister(request)
    print("somehin")
    print(request.POST)

    # Save the user's result and
    # make sure they selected something for every office.
    for office in offices:
      try:
        interest = request.POST[str(office.id)]
        print(interest)
      except:
        # User didn't selected something for every office
        context['error'] = True
        return render(request, 'elections/ois_submission.html', context)


  return render(request, 'elections/ois_submission.html', context)

def ois_results(request):
  return render(request, 'elections/ois_results.html', {})

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

