from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import Event, Sister

def events(request):
  events = Event.objects.order_by('-date');
  return render(request, 'attendance/events.html', {'events': events})

def checkin(request, event_id):
  # TODO
  event = get_object_or_404(Event, pk=event_id)
  required_sisters = Sister.objects.exclude(status=Sister.ALUM).exclude(status=Sister.ABROAD)
  context = {
    'event': event,
    'sisters': required_sisters,
  }
  return render(request, 'attendance/checkin.html', context)
  #return HttpResponse("Checkin for event %s." % event_id)