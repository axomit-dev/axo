from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
  return render(request, 'house/index.html', {})

@login_required
def dinner(request):
  return render(request, 'house/dinner.html', {})

@login_required
def parking(request):
  return render(request, 'house/parking.html', {})