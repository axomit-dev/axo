from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Event, User, Excuse, Semester
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

# Returns all the information necessary for a full attendance record
# for the given sister in the given semester.
# Assumes that both sister and semester_id are valid.
def get_sister_record(sister, semester_id):
  semester = Semester.objects.get(id=semester_id)
  time_threshold = timezone.now()
  #date__lte means 'date is less than or equal to'
  past_events = Event.objects.filter(semester=semester, date__lte=time_threshold).order_by('-date')
  future_events = Event.objects.filter(semester=semester, date__gt=time_threshold).order_by('-date')

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

  semesters = Semester.objects.all()
  context = {
    'sister': sister,
    'past_events': past_events,
    'future_events_and_excuses': future_events_and_excuses,
    'semesters': semesters,
    'current_semester': semester,
  }
  return context


#######################
##### BASIC VIEWS #####
#######################

# Homepage
def index(request):
  # Set latest_semester session variable
  # to use when rendering attendance for a default semester
  #request.session['latest_semester'] = latest_semester.id
  latest_semester = Semester.objects.all()[0]
  return render(request, 'attendance/index.html', {'semester': latest_semester})


###############################
##### EVENT-RELATED VIEWS #####
###############################

# List of all events
@user_passes_test(lambda u: u.is_staff)
def events(request):
  events = Event.objects.order_by('-date')
  # Get years for activation button
  years_query = Sister.objects.values('class_year').distinct()
  years_list = [x['class_year'] for x in years_query]
  # Order latest to earliest
  years_list.sort()
  years_list.reverse()
  context = {
    'events': events,
    'years': years_list,
  }
  return render(request, 'attendance/events.html', context)

# Detail page for a specific event
@user_passes_test(lambda u: u.is_staff)
def event_details(request, event_id):
  event = get_object_or_404(Event, pk=event_id)
  if (event.is_activated):
    # Event has been activated

    # Get fraction attended, excused, and absent
    # The excused set and attended set should be mutually exclusive
    num_required = len(event.sisters_required.all())

    # TODO: Display something if no required sisters?
    if num_required == 0:
      percent_attended = 0
      percent_excused = 0
      percent_absent = 0
    else:
      fraction_attended = len(event.sisters_attended.all())*1.0 / num_required
      fraction_excused = len(event.sisters_excused.all())*1.0 / num_required
      fraction_absent = 1.0 - fraction_attended - fraction_excused

      # Convert fraction to 2-digit integer for percentage
      percent_attended = int(round(fraction_attended*100, 0))
      percent_excused = int(round(fraction_excused*100, 0))
      percent_absent = int(round(fraction_absent*100, 0))

    context = {
      'percent_attended': percent_attended,
      'percent_excused': percent_excused,
      'percent_absent': percent_absent,
      'event': event,
    }
    return render(request, 'attendance/event_details.html', context)
  else:
    # TODO: use render with a different context
    return HttpResponse("This event has not been activated yet.") 

# Activate an event.
# This records a list of sisters who should be attending, based
# on the status of all sisters. Anyone that isn't abroad, an alum,
# or deaffiliated is considered a possible attendee.
@user_passes_test(lambda u: u.is_staff)
def activate(request, event_id):  
  # Create the list of sisters who should attend
  required_group = request.POST['activate_group']
  if (required_group == 'all'):
    sisters_required = Sister.objects.exclude(status=Sister.ALUM).exclude(status=Sister.ABROAD).exclude(status=Sister.DEAFFILIATED)
  elif (required_group == 'new_members'):
    sisters_required = Sister.objects.filter(status=Sister.NEW_MEMBER)
  else:
    # Value is a year
    year = int(required_group)
    sisters_required = Sister.objects.filter(class_year=year).exclude(status=Sister.ALUM).exclude(status=Sister.ABROAD).exclude(status=Sister.DEAFFILIATED)

  event = get_object_or_404(Event, pk=event_id)
  event.sisters_required = sisters_required
  event.is_activated = True
  event.save()
  # Redirect to the event details page
  return HttpResponseRedirect(
    reverse('attendance:event_details', args=(event.id,)))

# Check-in a particular sister for a particular event.
@user_passes_test(lambda u: u.is_staff)
def checkin_sister(request, event_id, sister_id):
  event = get_object_or_404(Event, pk=event_id)
  sister = get_object_or_404(Sister, pk=sister_id)
  # Add sister to list of attendees
  event.sisters_attended.add(sister)
  # Remove from excused absences to avoid duplication
  event.sisters_excused.remove(sister)
  event.save()
  # Redirect to the same event details page
  return HttpResponseRedirect(
    reverse('attendance:event_details', args=(event.id,)))


################################
##### SISTER-RELATED VIEWS #####
################################

# View attendance record of the logged-in user.
@login_required
def personal_record(request, semester_id):
  sister = get_sister(request)
  context = get_sister_record(sister, semester_id)
  return render(request, 'attendance/personal_record.html', context)

# View a list of all sisters.
@user_passes_test(lambda u: u.is_superuser)
def sisters(request):
  active_sisters = Sister.objects.exclude(status=Sister.ALUM).exclude(stauts=Sister.DEAFFILIATED)
  latest_semester = Semester.objects.all()[0]
  context = {
    'sisters': active_sisters,
    'semester': latest_semester,
  }
  return render(request, 'attendance/sisters.html', context)

# View the attendance record of the sister with sister_id.
@user_passes_test(lambda u: u.is_superuser)
def sister_record(request, sister_id, semester_id):
  sister = Sister.objects.get(id=sister_id)
  context = get_sister_record(sister, semester_id)
  return render(request, 'attendance/sister_record.html', context)


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

  latest_semester = Semester.objects.all()[0]
  return HttpResponseRedirect(
    reverse('attendance:personal_record', args=(latest_semester.id,)))

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
  # if they haven't alreaady been checked in
  event = get_object_or_404(Event, pk=excuse.event.id)
  sister = get_object_or_404(Sister, pk=excuse.sister.id)
  if (sister not in event.sisters_attended.all()):
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