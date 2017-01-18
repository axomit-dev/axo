from django.shortcuts import render

def index(request):
  return render(request, 'general/index.html', {})

def credits(request):
  return render(request, 'general/credits.html', {})