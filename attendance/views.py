from django.shortcuts import render
from django.http import HttpResponse

from .models import Event, Sister

def events(request):
  events = Event.objects.order_by('-date');
  return render(request, 'attendance/events.html', {'events': events})

def checkin(request, event_id):
  # TODO
  required_sisters = Sister.objects.exclude(status=Sister.ALUM).exclude(status=Sister.ABROAD)
  return render(request, 'attendance/checkin.html', {'sisters': required_sisters})
  #return HttpResponse("Checkin for event %s." % event_id)