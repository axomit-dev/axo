from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from general.views import get_sister
from django.utils.datastructures import MultiValueDictKeyError

from .models import Event, User, Excuse, Semester
from general.models import Sister

#####################
##### CONSTANTS #####
#####################
no_percentage_available_message = "There have been no mandatory events that you've needed to attend yet!"
value_of_excused_absence = .75

##########################
##### HELPER METHODS #####
##########################

# Returns the correct semester ID.
# If request['semester'] is defined, that is the ID.
# Otherwise, use the ID of the latest semester in the database.
def get_semester_id(request):
  if request.GET.get('semester', False):
    # Semester was passed in as parameter
    return int(request.GET['semester'])
  else:
    # Otherwise, use the latest semester
    semester = Semester.objects.all()[0]
    return semester.id

# Returns all the information necessary for a full attendance record
# for the given sister in the given semester.
# Assumes that both sister and semester_id are valid.
def get_sister_record(sister, semester_id):
  semester = Semester.objects.get(id=semester_id)
  time_threshold = timezone.now()
  #date__lte means 'date is less than or equal to'
  past_events = Event.objects.filter(semester=semester, date__lte=time_threshold).order_by('-date')
  future_events = Event.objects.filter(semester=semester, date__gt=time_threshold).order_by('-date')

  # For past events, determine what points sister actually earned
  # TODO: Duplicate code from calculate percentage?
  overall_earned_points = 0
  overall_total_points = 0
  for event in past_events:
    if sister in event.sisters_required.all():
      if (sister in event.sisters_attended.all()) or (sister in event.sisters_freebied.all()):
        event.earned_points = event.points
      elif (sister in event.sisters_excused.all()):
        event.earned_points = value_of_excused_absence*event.points
      else:
        event.earned_points = 0
      event.save()
      overall_earned_points += event.earned_points
      if (event.is_mandatory):
        overall_total_points += event.points
    else:
      event.earned_points = "--"


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
    'percentage': format_percentage(calculate_percentage(sister, semester_id)),
    'overall_total_points': overall_total_points,
    'overall_earned_points': overall_earned_points,
  }
  return context

# Returns a sister's attendance for the given semester for events in the past.
# Attendance is returned as a float, where 1.0 represents 100% attendance.
# If there haven't been any mandatory events or this sister hasn't
#   been required at any events this semester, the no_percentage_available_message
#   will be returned instead.
# Assumes that both sister and semester_id are valid.
def calculate_percentage(sister,semester_id):
  semester = Semester.objects.get(id=semester_id)
  time_threshold = timezone.now()
  past_events = Event.objects.filter(semester=semester, date__lte=time_threshold)
  
  total_points=0
  earned_points=0

  for event in past_events:
    if (sister in event.sisters_required.all()):
      if (event.is_mandatory):
        total_points+=event.points
      if (sister in event.sisters_attended.all()) or (sister in event.sisters_freebied.all()):
        # A freebie earns 100% of the event points
        earned_points+=event.points
      elif sister in event.sisters_excused.all():
        earned_points+= value_of_excused_absence*event.points
    elif sister in event.sisters_attended.all() and sister not in event.sisters_required.all():
      earned_points+=event.points
  if total_points !=0:
    return float(earned_points)/float(total_points)
  else:
    return no_percentage_available_message

# Formats the fraction for display as an attendance percentage.
# If .80 <= fraction <= .90, returns the fraction as a percent
#   with two decimals and a percent sign.
#   Otherwise, if fraction is a number, returns the fraction
#   as a percent with 0 decimal places and a percent sign.
# If fraction = no_percentage_available_message, that will be returned.
def format_percentage(fraction):
  if (fraction != no_percentage_available_message):
    # If they're within 85%, be more granular
    if abs(fraction - .85) <= .05:
      return str(round(fraction*100, 2)) + "%"
    else:
      return str(int(round(fraction*100, 0))) + "%"
  return fraction


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

# List of all events for the given semester
@user_passes_test(lambda u: u.is_staff)
def events(request):
  # Get all events for this semester
  semester_id = get_semester_id(request)
  semester = Semester.objects.get(id=semester_id)
  events = Event.objects.filter(semester=semester).order_by('-date')
  # Get years for activation button
  years_query = Sister.objects.values('class_year').distinct()
  years_list = [x['class_year'] for x in years_query]
  # Order latest to earliest
  years_list.sort()
  years_list.reverse()

  semesters = Semester.objects.all()
  context = {
    'events': events,
    'years': years_list,
    'semesters': semesters,
    'current_semester': semester,
    'semester_tab_url': 'attendance:events'
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
      fraction_excused = (len(event.sisters_excused.all()) + len(event.sisters_freebied.all()))*1.0 / num_required
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
  # Removed from freebied absences to avoid duplication
  event.sisters_freebied.remove(sister)
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
  semester_id = get_semester_id(request)
  context = get_sister_record(sister, semester_id)
  context['semester_tab_url'] = "attendance:personal_record"
  return render(request, 'attendance/personal_record.html', context)

# View a list of all sisters and their percentages.
@user_passes_test(lambda u: u.is_superuser)
def sisters(request):
  semester_id = get_semester_id(request)
  semester = Semester.objects.get(id=semester_id)
  active_sisters = Sister.objects.exclude(status=Sister.ALUM).exclude(status=Sister.DEAFFILIATED)

  # Calculate each sister's percentaage
  for sister in active_sisters:
    percent = calculate_percentage(sister, semester.id)
    sister.percentage = percent

  if request.GET.get('order_by_percent', False):
    # If order_by_percent = True, sort sisters by percentage,
    # lowest percentage first
    def sort_func(sister):
      return sister.percentage
    sorted_sisters = sorted(active_sisters, key=sort_func)
  else:
    # Otherwise, sort sisters alphabetically
    # Sisters are already sorted, so don't need to do anything
    sorted_sisters = active_sisters

  # Format the percentage correctly after using it for sorting
  def format(sister):
    sister.percentage = format_percentage(sister.percentage)
    return sister
  sorted_sisters = [format(sister) for sister in sorted_sisters]

  context = {
    'sisters': sorted_sisters,
    'current_semester': semester,
    'semesters': Semester.objects.all(),
    'semester_tab_url': 'attendance:sisters',
  }
  return render(request, 'attendance/sisters.html', context)

# View the attendance record of the sister with sister_id.
@user_passes_test(lambda u: u.is_superuser)
def sister_record(request, sister_id):
  semester_id = get_semester_id(request)
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
  sister = get_sister(request)
  # Display the page
  if request.method == 'GET':
    context = {
      'event': event,
    }
    # See if sister has already used freebie before
    # Doesn't look at status of excuse since it assumes
    # all freebie requests will be granted. Alternatively,
    # could validate during approving excuse that this is
    # the first freebie of the semester.
    freebie_excuses = Excuse.objects.filter(
      sister=sister, is_freebie=True, event__semester=event.semester)
    print(freebie_excuses)
    if len(freebie_excuses) > 0:
      context['used_freebie'] = True
    else:
      # They haven't used a freebie this semester
      context['used_freebie'] = False
    print(context)
    return render(request, 'attendance/excuse_form.html', context)
  
  # Save the submitted data
  elif request.method == 'POST':
    # See if they chose it as a freebie
    try:
      freebie = request.POST['is_freebie']
      using_freebie = True
    except MultiValueDictKeyError:
      # They didn't check the box
      using_freebie = False

    # Save excuse
    # TODO: Make sure there isn't already an existing excuse?
    excuse_text = request.POST['excuse']
    excuse = Excuse(event=event, sister=sister, text=excuse_text, is_freebie=using_freebie)
    excuse.save()

    # Redirect to the personal record page, to the semester
    # that the event is from
    return HttpResponseRedirect(
      reverse('attendance:personal_record', args=(event.semester.id,)))
  

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

  # Add that sister to list of excused or freebie sisters
  # if they haven't alreaady been checked in
  event = get_object_or_404(Event, pk=excuse.event.id)
  sister = get_object_or_404(Sister, pk=excuse.sister.id)
  if (sister not in event.sisters_attended.all()):
    if (excuse.is_freebie):
      event.sisters_freebied.add(sister)
    else:
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
