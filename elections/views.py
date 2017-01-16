from django.shortcuts import render

def index(request):
  return render(request, 'elections/index.html', {})

def ois_submission(request):
  return render(request, 'elections/ois_submission.html', {})

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

