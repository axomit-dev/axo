from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from .models import Event, Sister

def index(request):
  return render(request, 'attendance/index.html', {})

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

def checkin_sister(request, event_id, sister_id):
  event = get_object_or_404(Event, pk=event_id)
  sister = get_object_or_404(Sister, pk=sister_id)
  # Add sister to list of attendees
  event.sisters_attended.add(sister)
  event.save()
  # Redirect to the same checkin page
  return HttpResponseRedirect(
    reverse('attendance:checkin', args=(event.id,)))


