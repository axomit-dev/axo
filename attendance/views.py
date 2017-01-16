from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import Event, Sister, User, Excuse

# Helper method to fill in user and sister if someone is logged in.
def get_context(request):
  context = {}
  context['user'] = request.user
  if request.user.is_authenticated():
    try:
      context['sister'] = Sister.objects.get(user=request.user)
    except:
      pass
  return context

# Helper method to get the current sister logged in.
def get_sister(request):
  context = get_context(request)
  if context['sister']:
    return context['sister']
  else:
    return None

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

# View attendance record of the given user.
@login_required
def personal_record(request):
  request_context = get_context(request)
  #user = get_object_or_404(User, pk=user_id)
  #sister = get_object_or_404(Sister, user=user)
  all_events = Event.objects.order_by('-date');
  context = {
    'sister': request_context['sister'],
    'events': all_events,
  }
  return render(request, 'attendance/personal_record.html', context)


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



# EXCUSE-RELATED VIEWS

# Render the page to write an excuse.
@login_required
def excuse_write(request, event_id):
  sister = get_sister(request)
  event = get_object_or_404(Event, pk=event_id)
  context = {
    'event': event
  }
  # See if they've already written an excuse for this event.
  try:
    excuse = Excuse.objects.get(sister=sister, event=event)
  except Excuse.DoesNotExist:
    pass
  else:
    context['excuse'] = excuse

  return render(request, 'attendance/excuse_write.html', context)

# Handle the POST request to submit an excuse.
@login_required
def excuse_submit(request, event_id):
  event = get_object_or_404(Event, pk=event_id)
  excuse_text = request.POST['excuse']
  print(excuse_text)
  sister = get_sister(request)
  excuse = Excuse(event=event, sister=sister, text=excuse_text)
  excuse.save()
  return HttpResponseRedirect(
    reverse('attendance:excuse_write', args=(event.id,)))