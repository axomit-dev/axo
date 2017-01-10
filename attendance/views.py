from django.shortcuts import render

from .models import Event

def events(request):
  events = Event.objects.order_by('-date');
  return render(request, 'attendance/events.html', {'events': events})