from django.shortcuts import render
from django.http import HttpResponse

def index(request):
  return render(request, 'general/index.html', {})

def credits(request):
  return render(request, 'general/credits.html', {})