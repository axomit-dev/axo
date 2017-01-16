from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Event, User, Excuse
from general.models import Sister

##########################
##### HELPER METHODS #####
##########################

# Returns dictionary with user and sister if someone is logged in.
def get_context(request):
  context = {}
  context['user'] = request.user
  if request.user.is_authenticated():
    try:
      context['sister'] = Sister.objects.get(user=request.user)
    except:
      pass
  return context

# Returns the current sister logged in, if there is one.
def get_sister(request):
  context = get_context(request)
  if context['sister']:
    return context['sister']
  else:
    return None


#######################
##### BASIC VIEWS #####
#######################

# Homepage
def index(request):
  return render(request, 'attendance/index.html', {})


###############################
##### EVENT-RELATED VIEWS #####
###############################

# List of all events
@user_passes_test(lambda u: u.is_superuser)
def events(request):
  events = Event.objects.order_by('-date');
  return render(request, 'attendance/events.html', {'events': events})

# Detail page for a specific event
@user_passes_test(lambda u: u.is_superuser)
def event_details(request, event_id):
  event = get_object_or_404(Event, pk=event_id)
  if (event.is_activated):
    # Event has been activated
    return render(request, 'attendance/event_details.html', {'event': event})
  else:
    return HttpResponse("This event has not been activated yet.") 

# Activate an event.
# This records a list of sisters who should be attending, based
# on the status of all sisters. Anyone that isn't abroad or an alum
# is considered a possible attendee.
@user_passes_test(lambda u: u.is_superuser)
def activate(request, event_id):  
  # Create the list of sisters who should attend
  required_group = request.POST['activate_group']
  if (required_group == 'all'):
    sisters_required = Sister.objects.exclude(status=Sister.ALUM).exclude(status=Sister.ABROAD)
  elif (required_group == 'new_members'):
    sisters_required = Sister.objects.filter(status=Sister.NEW_MEMBER)
  else:
    # Value is a year
    year = int(required_group)
    sisters_required = Sister.objects.filter(class_year=year).exclude(status=Sister.ALUM).exclude(status=Sister.ABROAD)

  event = get_object_or_404(Event, pk=event_id)
  event.sisters_required = sisters_required
  event.is_activated = True
  event.save()
  # Redirect to the event details page
  return HttpResponseRedirect(
    reverse('attendance:event_details', args=(event.id,)))

# Check-in a particular sister for a particular event.
@user_passes_test(lambda u: u.is_superuser)
def checkin_sister(request, event_id, sister_id):
  event = get_object_or_404(Event, pk=event_id)
  sister = get_object_or_404(Sister, pk=sister_id)
  # Add sister to list of attendees
  event.sisters_attended.add(sister)
  event.save()
  # Redirect to the same event details page
  return HttpResponseRedirect(
    reverse('attendance:event_details', args=(event.id,)))


################################
##### SISTER-RELATED VIEWS #####
################################

# View attendance record of the logged-in user.
@login_required
def personal_record(request):
  sister = get_sister(request)
  time_threshold = timezone.now()
  #date__lte means 'date is less than or equal to'
  past_events = Event.objects.filter(date__lte=time_threshold).order_by('-date')
  future_events = Event.objects.filter(date__gt=time_threshold).order_by('-date')

  # List of events and excuses
  # If the item is an excuse, then there is an excuse associated
  #    with that event for this particular sister.
  # Otherwise, the item is an event and there is no associated excuse.
  future_events_and_excuses = []
  for event in future_events:
    try:
      excuse = Excuse.objects.get(event=event, sister=sister)
    except Excuse.DoesNotExist:
      future_events_and_excuses.append(event)
    else:
      future_events_and_excuses.append(excuse)

  context = {
    'sister': sister,
    'past_events': past_events,
    'future_events_and_excuses': future_events_and_excuses,
  }
  return render(request, 'attendance/personal_record.html', context)


################################
##### EXCUSE-RELATED VIEWS #####
################################

# Handle the POST request to submit an excuse.
@login_required
def excuse_submit(request, event_id):
  event = get_object_or_404(Event, pk=event_id)
  excuse_text = request.POST['excuse']
  sister = get_sister(request)
  excuse = Excuse(event=event, sister=sister, text=excuse_text)
  excuse.save()
  return HttpResponseRedirect(
    reverse('attendance:personal_record'))

# Display all pending excuses.
@user_passes_test(lambda u: u.is_superuser)
def excuse_pending(request):
  excuses = Excuse.objects.filter(status=Excuse.PENDING)
  return render(request, 'attendance/excuse_pending.html', {'excuses': excuses})

# Approve an excuse.
@user_passes_test(lambda u: u.is_superuser)
def excuse_approve(request, excuse_id):
  excuse = get_object_or_404(Excuse, pk=excuse_id)
  excuse.status = Excuse.APPROVED
  excuse.save()

  # Add that sister to list of excused sisters
  event = get_object_or_404(Event, pk=excuse.event.id)
  sister = get_object_or_404(Sister, pk=excuse.sister.id)
  event.sisters_excused.add(sister)
  event.save()

  # Email sister with result
  if (sister.user.email):
    message = 'Your excuse is approved. \n' + \
      'For reference, here is the excuse you submitted: \n' + \
      excuse.text
    send_mail(
      'Excuse for ' + event.__str__(),
      message,
      settings.EMAIL_HOST_USER,
      [sister.user.email],
      fail_silently=False,
    )

  # Go back to list of pending excuses
  return HttpResponseRedirect(
    reverse('attendance:excuse_pending'))

# Deny an excuse.
@user_passes_test(lambda u: u.is_superuser)
def excuse_deny(request, excuse_id):
  excuse = get_object_or_404(Excuse, pk=excuse_id)
  excuse.status = Excuse.DENIED
  excuse.save()

  # Email sister with result
  sister = get_object_or_404(Sister, pk=excuse.sister.id)
  event = get_object_or_404(Event, pk=excuse.event.id)
  if (sister.user.email):
    message = 'Your excuse is denied. \n' + \
      'For reference, here is the excuse you submitted: \n' + \
      excuse.text
    send_mail(
      'Excuse for ' + event.__str__(),
      message,
      settings.EMAIL_HOST_USER,
      [sister.user.email],
      fail_silently=False,
    )

  return HttpResponseRedirect(
    reverse('attendance:excuse_pending'))