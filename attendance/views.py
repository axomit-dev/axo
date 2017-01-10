from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from .models import Event, Sister

def events(request):
  print("displaying events")
  events = Event.objects.order_by('-date');
  return render(request, 'attendance/events.html', {'events': events})

def checkin(request, event_id):
  event = get_object_or_404(Event, pk=event_id)
  if (event.is_activated):
    # Event has been activated
    return render(request, 'attendance/checkin.html', {'event': event})
  else:
    return HttpResponse("This event has not been activated yet.")  

def activate(request, event_id):
  event = get_object_or_404(Event, pk=event_id)
  # Create the list of sisters who should attend
  required_sisters = Sister.objects.exclude(status=Sister.ALUM).exclude(status=Sister.ABROAD)
  event.required_sisters = required_sisters
  event.is_activated = True
  event.save()
  # Redirect to the checkin page
  return HttpResponseRedirect(
    reverse('attendance:checkin', args=(event.id,)))

