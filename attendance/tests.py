import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Event, Semester, Excuse
from . import views
from general.models import Sister

test_email = 'axo.mit.attendance@gmail.com'

##########################
##### HELPER METHODS #####
##########################

def create_event(event_name, days, points, semester=None, is_mandatory=False, is_activated=False):
  """
  Helper method to create an event.
  days is the number of days offset from now at 5am that the event occurs.
  A negative number means the event was in the past.
  Returns the new event.
  """
  # 5AM because of our timezone relative to UTC.
  time = timezone.now() + datetime.timedelta(days=days)
  if not semester:
    semester = Semester.objects.create(term=Semester.SPRING, year=2000)
  return Event.objects.create(name=event_name, date=time, points=points, semester=semester, is_mandatory=is_mandatory, is_activated=is_activated)


# Creates and logs in a normal user.
# Returns that user.
def create_and_login_user(client, username, password, is_superuser=False, email=None):
  if is_superuser:
    User.objects.create_superuser(username=username, password=password, email=email)
  else:
    User.objects.create_user(username=username, password=password)
  result = client.login(username=username, password=password)
  return User.objects.get(username=username)

# Creates and returns a sister that has the given username, status, and class year.
def create_sister(username, status, class_year):
  user = User.objects.create_user(username=username, password='aoisdj')
  sister = Sister.objects.create(user=user, status=status, class_year=class_year)
  return sister

# Creates and returns a semester
def create_semester(term, year):
  semester = Semester.objects.create(term=term, year=year)
  return semester

# Creates and returns an excuse
def create_excuse(event, sister, text, status=Excuse.PENDING):
  excuse = Excuse.objects.create(event=event, sister=sister, text=text, status=status)
  return excuse

######################################
##### CALCULATE_PERCENTAGE TESTS #####
######################################
class CalculatePercentageTests(TestCase):
  def test_calculate_percentage_no_events(self):
    sister = create_sister('michal', Sister.ACTIVE, 2019)
    semester = create_semester(Semester.FALL, 2017)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_no_events_in_given_semester(self):
    sister = create_sister('sis', Sister.ACTIVE, 2016)
    semester = create_semester(Semester.FALL, 2017)
    semester_of_event = create_semester(Semester.SPRING, 2017)
    event = create_event("future", days=3, points=10, semester=semester_of_event)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_one_past_mandatory_event_attended(self):
    sister = create_sister("reb", Sister.ACTIVE, 2019)
    semester = create_semester(Semester.FALL, 2018)
    event = create_event("yo", -1, 30, semester=semester, is_mandatory=True)
    event.sisters_required.add(sister)
    event.sisters_attended.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, 1.0)

  def test_calculate_percentage_one_past_mandatory_event_excused(self):
    sister = create_sister("reb", Sister.ACTIVE, 2019)
    semester = create_semester(Semester.FALL, 2018)
    event = create_event("yo", -2, 30, semester=semester, is_mandatory=True)
    event.sisters_required.add(sister)
    event.sisters_excused.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, .75)

  def test_calculate_percentage_one_past_mandatory_event_absent(self):
    sister = create_sister("reb", Sister.ACTIVE, 2019)
    semester = create_semester(Semester.FALL, 2018)
    event = create_event("yo", -6, 30, semester=semester, is_mandatory=True)
    event.sisters_required.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, 0.0)

  def test_calculate_percentage_one_past_mandatory_event_not_required_to_attend(self):
    sister = create_sister("reb", Sister.ACTIVE, 2019)
    semester = create_semester(Semester.FALL, 2018)
    event = create_event("yo", -40, 30, semester=semester, is_mandatory=True)

    percentage = views.calculate_percentage(sister, semester.id)

    # Since they haven't needed to attend any events, can't calculate a percentage
    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_one_past_non_mandatory_event_attended(self):
    sister = create_sister("reb", Sister.ACTIVE, 2019)
    semester = create_semester(Semester.FALL, 2018)
    event = create_event("yo", -1000, 30, semester=semester, is_mandatory=False)
    event.sisters_required.add(sister)
    event.sisters_attended.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    # Since there's no mandatory events yet, can't calculate a percentage
    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_two_past_events_one_mandatory(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event_mandatory = create_event("chapter", -2, 20, semester=semester, is_mandatory=True)
    event_not = create_event("mixer", -5, 10, semester=semester, is_mandatory=False)

    event_mandatory.sisters_required.add(sister)
    event_not.sisters_required.add(sister)
    event_not.sisters_attended.add(sister)
    # Total points = 20, earned points = 10

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, .5)

  def test_calculate_percentage_over_one_hundred_percent(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event_mandatory = create_event("chapter", -20, 20, semester=semester, is_mandatory=True)
    event_not = create_event("mixer", -6, 12, semester=semester, is_mandatory=False)

    event_mandatory.sisters_required.add(sister)
    event_mandatory.sisters_excused.add(sister)
    event_not.sisters_required.add(sister)
    event_not.sisters_attended.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    earned_points = 12 + (Event.VALUE_OF_EXCUSED_ABSENCE*20)
    expected_percentage = earned_points / 20.0 # = 1.35
    self.assertEqual(percentage, expected_percentage)

  def test_calculate_percentage_many_past_events_same_semester(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event_mandatory1 = create_event("chapter", -2, 20, semester=semester, is_mandatory=True)
    event_mandatory2 = create_event("chapter2", -14, 30, semester=semester, is_mandatory=True)
    event_not_mandatory1 = create_event("mixer", -5, 12, semester=semester, is_mandatory=False)
    event_not_mandatory2 = create_event("mixer2", -12, 10, semester=semester, is_mandatory=False)

    event_mandatory1.sisters_required.add(sister)
    event_mandatory2.sisters_required.add(sister)
    event_not_mandatory1.sisters_required.add(sister)
    event_not_mandatory2.sisters_required.add(sister)
    event_not_mandatory1.sisters_attended.add(sister)
    event_not_mandatory2.sisters_attended.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    mandatory_points = 20 + 30
    earned_points = 12 + 10
    expected_percentage = earned_points*1.0 / mandatory_points
    self.assertEqual(percentage, expected_percentage)

  def test_calculate_percentage_many_past_events_different_semesters(self):
    sister = create_sister("aw;elif", Sister.ABROAD, 2018)
    semester1 = create_semester(Semester.SPRING, 2016)
    semester2 = create_semester(Semester.FALL, 2016)
    event_sem1_mand = create_event("initiation", days=-10, points=50, semester=semester1, is_mandatory=True)
    event_sem1_notmand = create_event("idkman", days=-1, points=15, semester=semester1, is_mandatory=False)
    event_sem2_mand = create_event("dva shifts", days=-20, points=20, semester=semester2, is_mandatory=True)

    event_sem1_mand.sisters_required.add(sister)
    event_sem1_notmand.sisters_required.add(sister)
    event_sem2_mand.sisters_required.add(sister)
    event_sem1_mand.sisters_excused.add(sister)
    event_sem2_mand.sisters_attended.add(sister)

    # Get percentage for semester1
    percentage = views.calculate_percentage(sister, semester1.id)

    mandatory_points = 50
    earned_points = Event.VALUE_OF_EXCUSED_ABSENCE*50
    expected_percentage = earned_points*1.0 / mandatory_points
    self.assertEqual(percentage, expected_percentage)

  def test_caclulate_percentage_many_past_events_many_semesters_many_sisters(self):
    sister = create_sister("aw;elif", Sister.ABROAD, 2018)
    sister_other = create_sister("button smash", Sister.ACTIVE, 2017)
    semester1 = create_semester(Semester.SPRING, 2016)
    semester2 = create_semester(Semester.FALL, 2016)
    event_sem1_mand = create_event("initiation", days=-10, points=50, semester=semester1, is_mandatory=True)
    event_sem1_mand2 = create_event("my journey 2018s", days=-1, points=20, semester=semester1, is_mandatory=True)
    event_sem1_notmand = create_event("idkman", days=-1, points=15, semester=semester1, is_mandatory=False)
    event_sem1_notmand2 = create_event("2017 fireside", days=-20, points=10, semester=semester1, is_mandatory=False)
    event_sem2_mand = create_event("dva shifts", days=-20, points=20, semester=semester2, is_mandatory=True)
    event_sem2_notmand = create_event("zeta psi mixer", days=-5, points=5, semester=semester2, is_mandatory=False)

    # sister required at everything except 2017 fireside
    event_sem1_mand.sisters_required.add(sister)
    event_sem1_mand2.sisters_required.add(sister)
    event_sem1_notmand.sisters_required.add(sister)
    event_sem2_mand.sisters_required.add(sister)
    event_sem2_notmand.sisters_required.add(sister)

    # sister_other required at everything except 2018 my journey
    event_sem1_mand.sisters_required.add(sister_other)
    event_sem1_notmand.sisters_required.add(sister_other)
    event_sem1_notmand2.sisters_required.add(sister_other)
    event_sem2_mand.sisters_required.add(sister_other)
    event_sem2_notmand.sisters_required.add(sister_other)

    event_sem1_mand.sisters_attended.add(sister)
    event_sem1_notmand.sisters_attended.add(sister)
    event_sem2_mand.sisters_attended.add(sister)

    event_sem1_mand.sisters_attended.add(sister_other)
    event_sem1_notmand2.sisters_attended.add(sister_other)
    event_sem2_mand.sisters_excused.add(sister_other)

    # Get percentage for semester1 for normal sister
    percentage = views.calculate_percentage(sister, semester1.id)

    mandatory_points = 50 + 20
    earned_points = 50 + 15
    expected_percentage = earned_points*1.0 / mandatory_points
    self.assertEqual(percentage, expected_percentage)

  def test_calculate_percentage_one_future_event(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event = create_event("chapter", 40, 20, semester=semester, is_mandatory=True)
    event.sisters_required.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_one_future_event_attended(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event = create_event("chapter", 1, 20, semester=semester, is_mandatory=True)
    event.sisters_required.add(sister)
    event.sisters_attended.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_one_future_event_excused(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event = create_event("chapter", 2, 20, semester=semester, is_mandatory=True)

    event.sisters_required.add(sister)
    event.sisters_excused.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_future_events_and_past_events_not_required(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event = create_event("chapter", 2, 20, semester=semester, is_mandatory=True)
    event_past = create_event("idk", -2, 13, semester=semester, is_mandatory=True)

    event.sisters_required.add(sister)
    event.sisters_excused.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, views.no_percentage_available_message)

  def test_calculate_percentage_future_and_past_events_same_semester(self):
    sister = create_sister("siena", Sister.ACTIVE, 2018)
    semester = create_semester(Semester.FALL, 2017)
    event_past1 = create_event("chapter", -20, 20, semester=semester, is_mandatory=True)
    event_past2 = create_event("mixer", -6, 12, semester=semester, is_mandatory=False)
    event_future1 = create_event("chapter2", 60, 58, semester=semester, is_mandatory=True)
    event_future2 = create_event("mixer2", 6, 11, semester=semester, is_mandatory=False)

    event_past1.sisters_required.add(sister)
    event_past1.sisters_attended.add(sister)
    event_past2.sisters_required.add(sister)
    event_future1.sisters_required.add(sister)
    event_future2.sisters_required.add(sister)
    event_future1.sisters_excused.add(sister)

    percentage = views.calculate_percentage(sister, semester.id)

    self.assertEqual(percentage, 1.0)

  def test_calculate_percentage_future_and_past_events_different_semesters(self):
    sister = create_sister("aw;elif", Sister.ABROAD, 2018)
    semester1 = create_semester(Semester.SPRING, 2016)
    semester2 = create_semester(Semester.FALL, 2016)

    # Past
    event_sem1_mand = create_event("initiation", days=-10, points=25, semester=semester1, is_mandatory=True)
    event_sem1_notmand = create_event("idkman", days=-1, points=20, semester=semester1, is_mandatory=False)
    event_sem2_mand = create_event("dva shifts", days=-20, points=10, semester=semester2, is_mandatory=True)

    # Future
    event_sem1_future_mand = create_event("bid night", days=25, points=30, semester=semester1, is_mandatory=True)
    event_sem2_future_mand = create_event("first day of classes", days=10, points=10, semester=semester2, is_mandatory=True)
    event_sem2_future_notmand =  create_event("something", days=40, points=20, semester=semester2, is_mandatory=False)

    # Past
    event_sem1_mand.sisters_required.add(sister)
    event_sem1_notmand.sisters_required.add(sister)
    event_sem2_mand.sisters_required.add(sister)
    event_sem1_mand.sisters_attended.add(sister)
    event_sem1_notmand.sisters_attended.add(sister)
    event_sem2_mand.sisters_excused.add(sister)

    # Future
    event_sem1_future_mand.sisters_required.add(sister)
    event_sem2_future_mand.sisters_required.add(sister)
    event_sem2_future_notmand.sisters_required.add(sister)
    event_sem1_future_mand.sisters_excused.add(sister)
    event_sem2_future_notmand.sisters_attended.add(sister)

    # Get percentage for semester1
    percentage = views.calculate_percentage(sister, semester1.id)

    # Points for semester 1 past events only
    mandatory_points = 25
    earned_points = 20 + 25
    expected_percentage = earned_points*1.0 / mandatory_points
    self.assertEqual(percentage, expected_percentage)


###################################
##### GET_SISTER_RECORD TESTS #####
###################################
class GetSisterRecordTests(TestCase):
  def test_get_sister_record_no_events(self):
    sister = create_sister('ccassidy', Sister.ACTIVE, 2018)
    semester1 = create_semester(Semester.FALL, 2017)
    semester2 = create_semester(Semester.SPRING, 2018)

    context = views.get_sister_record(sister, semester1.id)

    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 0)
    self.assertEqual(len(context['future_events_and_excuses']), 0)
    self.assertEqual(context['current_semester'], semester1)
    self.assertEqual(len(context['semesters']), 2)
    self.assertEqual(semester1 in context['semesters'], True)
    self.assertEqual(semester2 in context['semesters'], True)

  def test_get_sister_record_one_future_event_in_semester(self):
    sister = create_sister('bro', Sister.ACTIVE, 2016)
    semester = create_semester(Semester.FALL, 2017)
    event = create_event("future", days=3, points=10, semester=semester)

    context = views.get_sister_record(sister, semester.id)

    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 0)
    self.assertEqual(len(context['future_events_and_excuses']), 1)
    self.assertEqual(event in context['future_events_and_excuses'], True)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 1)
    self.assertEqual(semester in context['semesters'], True)

  def test_get_sister_record_one_future_event_not_in_semester(self):
    sister = create_sister('bro', Sister.ACTIVE, 2016)
    semester = create_semester(Semester.FALL, 2017)
    semester_of_event = create_semester(Semester.SPRING, 2017)
    event = create_event("future", days=3, points=10, semester=semester_of_event)

    context = views.get_sister_record(sister, semester.id)

    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 0)
    self.assertEqual(len(context['future_events_and_excuses']), 0)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 2)
    self.assertEqual(semester in context['semesters'], True)
    self.assertEqual(semester_of_event in context['semesters'], True)

  def test_get_sister_record_one_past_event_in_semester(self):
    sister = create_sister('bro', Sister.ACTIVE, 2016)
    semester = create_semester(Semester.FALL, 2017)
    event = create_event("past", days=-3, points=10, semester=semester)

    context = views.get_sister_record(sister, semester.id)

    
    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 1)
    self.assertEqual(event in context['past_events'], True)
    self.assertEqual(len(context['future_events_and_excuses']), 0)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 1)
    self.assertEqual(semester in context['semesters'], True)

  def test_get_sister_record_one_past_event_not_in_semester(self):
    sister = create_sister('bro', Sister.ACTIVE, 2016)
    semester = create_semester(Semester.FALL, 2017)
    semester_of_event = create_semester(Semester.SPRING, 2017)
    event = create_event("past", days=-3, points=10, semester=semester_of_event)

    context = views.get_sister_record(sister, semester.id)

    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 0)
    self.assertEqual(len(context['future_events_and_excuses']), 0)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 2)
    self.assertEqual(semester in context['semesters'], True)
    self.assertEqual(semester_of_event in context['semesters'], True)
  def test_get_sister_record_one_past_event_not_in_semester(self):
    sister = create_sister('bro', Sister.ACTIVE, 2016)
    semester = create_semester(Semester.FALL, 2017)
    semester_of_event = create_semester(Semester.SPRING, 2017)
    event = create_event("past", days=-3, points=10, semester=semester_of_event)

    context = views.get_sister_record(sister, semester.id)

    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 0)
    self.assertEqual(len(context['future_events_and_excuses']), 0)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 2)
    self.assertEqual(semester in context['semesters'], True)
    self.assertEqual(semester_of_event in context['semesters'], True)
  def test_get_sister_record_one_future_event_with_excuse(self):
    sister = create_sister("newbie", Sister.NEW_MEMBER, 2020)
    semester = create_semester(Semester.SPRING, 2025)
    event = create_event("chapter", 4, 20, semester)
    excuse = create_excuse(event, sister, "yo", Excuse.APPROVED)

    context = views.get_sister_record(sister, semester.id)

    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 0)
    self.assertEqual(len(context['future_events_and_excuses']), 1)
    self.assertEqual(excuse in context['future_events_and_excuses'], True)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 1)
    self.assertEqual(semester in context['semesters'], True)

  def test_get_sister_record_past_and_future_events(self):
    sister = create_sister("lee", Sister.ABROAD, 2019)
    semester = create_semester(Semester.SPRING, 2016)
    event_future1 = create_event("chapter", 4, 20, semester)
    event_future2 = create_event("fireside", 1, 10, semester)
    event_past1 = create_event("fondue", -2, 30, semester)
    event_past2 = create_event("house cleaning", -50, 30, semester)

    context = views.get_sister_record(sister, semester.id)

    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 2)
    self.assertEqual(event_past1 in context['past_events'], True)
    self.assertEqual(event_past2 in context['past_events'], True)
    self.assertEqual(len(context['future_events_and_excuses']), 2)
    self.assertEqual(event_future1 in context['future_events_and_excuses'], True)
    self.assertEqual(event_future2 in context['future_events_and_excuses'], True)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 1)
    self.assertEqual(semester in context['semesters'], True)

  def test_get_sister_record_past_and_future_events_and_excuses(self):
    sister = create_sister("lee", Sister.ABROAD, 2019)
    semester = create_semester(Semester.SPRING, 2016)
    event_future1 = create_event("chapter", 4, 20, semester)
    event_future2 = create_event("fireside", 1, 10, semester)
    event_past1 = create_event("fondue", -2, 30, semester)
    excuse_for_future1 = create_excuse(event_future1, sister, "imdying", Excuse.DENIED)
    
    context = views.get_sister_record(sister, semester.id)
   
    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 1)
    self.assertEqual(event_past1 in context['past_events'], True)
    self.assertEqual(len(context['future_events_and_excuses']), 2)
    self.assertEqual(excuse_for_future1 in context['future_events_and_excuses'], True)
    self.assertEqual(event_future2 in context['future_events_and_excuses'], True)
    self.assertEqual(context['current_semester'], semester)
    self.assertEqual(len(context['semesters']), 1)
    self.assertEqual(semester in context['semesters'], True)

  def test_get_sister_record_events_and_excuses_different_semesters(self):
    sister = create_sister("emma", Sister.PRC, 2017)
    semester1 = create_semester(Semester.SPRING, 2016)
    semester2 = create_semester(Semester.FALL, 2016)
    semester3 = create_semester(Semester.FALL, 2018)
    event_sem1_future1 = create_event("chapter1", 4, 20, semester1)
    event_sem1_future2 = create_event("chapter2", 1, 10, semester1)
    event_sem1_future3 = create_event("chapter3", 400,30, semester1)
    event_sem1_past1 = create_event("bro", -39, 32, semester1)
    event_sem1_past2 = create_event("bro2", -38, 2, semester1)
    excuse_sem1_future2 = create_excuse(event_sem1_future2, sister, "alkskdajf")
    excuse_sem1_past1 = create_excuse(event_sem1_past1, sister, "aslke", Excuse.APPROVED)

    event_sem2_future = create_event(";aoiij", 2, 30, semester2)
    event_sem2_past = create_event("wjwj", -9, 19, semester2)
    excuse_sem2_past = create_excuse(event_sem2_past, sister, "esi", Excuse.APPROVED)

    event_sem3_future = create_event("weoij", 25, 39, semester3)
    excuse_sem3_future = create_excuse(event_sem3_future, sister, "yo", Excuse.DENIED)

    
    context = views.get_sister_record(sister, semester1.id)
  
    self.assertEqual(context['sister'], sister)
    self.assertEqual(len(context['past_events']), 2)
    self.assertEqual(event_sem1_past1 in context['past_events'], True)
    self.assertEqual(event_sem1_past2 in context['past_events'], True)
    self.assertEqual(len(context['future_events_and_excuses']), 3)
    self.assertEqual(excuse_sem1_future2 in context['future_events_and_excuses'], True)
    self.assertEqual(event_sem1_future1 in context['future_events_and_excuses'], True)
    self.assertEqual(event_sem1_future3 in context['future_events_and_excuses'], True)
    self.assertEqual(context['current_semester'], semester1)
    self.assertEqual(len(context['semesters']), 3)
    self.assertEqual(semester1 in context['semesters'], True)
    self.assertEqual(semester2 in context['semesters'], True)
    self.assertEqual(semester3 in context['semesters'], True)


##########################
##### ACTIVATE TESTS #####
##########################

# TODO: Test the actual HTML that's returned?
class ActivateTests(TestCase):  
  # Activate an event without any sisters
  def test_activate_simple(self):
    # Create database objects
    event = create_event("new_event", 1, 10)
    user = create_and_login_user(self.client, 'joe', 'bro', True, test_email)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': 'all'})

    # Should redirect to event details page
    expected_redirect = reverse('attendance:event_details', args=(event.id,))
    self.assertRedirects(response, expected_redirect)
    # Event should be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, True)

  # Try to activate an event when not logged in
  def test_activate_not_logged_in(self):
    # Create database objects
    event = create_event("new_event", 1, 10)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': 'all'})

    # Should redirect to the login page
    redirect_url = '/login/?next=' + post_url
    self.assertRedirects(response, redirect_url)
    # Event shouldn't be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, False)

  # Try to activate an event as only a normal user
  def test_activate_normal_user_logged_in(self):
    # Create database objects
    event = create_event("new_event", 1, 10)
    user = create_and_login_user(self.client, 'joe', 'bro')

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': 'all'})

    # Should redirect to the login page
    redirect_url = '/login/?next=' + post_url
    self.assertRedirects(response, redirect_url)
    # Event shouldn't be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, False)
    # TODO: Login page should say insufficient permissions
    # expected_text = "attendance"
    # self.assertContains(response, text=expected_text, status_code=302, html=True)

  # Try to activate an invalid event
  def test_activate_invalid_event(self):
    user = create_and_login_user(self.client, 'joe', 'bro', True, test_email)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': 5})
    response = self.client.post(post_url, {'activate_group': 'all'})

    # Should give 404
    self.assertEqual(response.status_code, 404)

  # TODO: Idk what this should do
  def test_activate_invalid_group(self):
    self.assertEqual(True, True)

  # Activate an event that is for everyone
  def test_activate_all(self):
    event = create_event("chapter", 3, 20)
    superuser = create_and_login_user(self.client, 'bob', 'siewj', True, test_email)

    # Sisters of all statuses and years
    sister1 = create_sister('active2018', Sister.ACTIVE, 2018)
    sister2 = create_sister('alum2015', Sister.ALUM, 2015)
    sister3 = create_sister('abroad2018', Sister.ABROAD, 2018)
    sister4 = create_sister('newmembie2020', Sister.NEW_MEMBER, 2020)
    sister5 = create_sister('prc2017', Sister.PRC, 2017)
    sister6 = create_sister('active2019', Sister.ACTIVE, 2019)
    sister10 = create_sister('deaffiliated2020', Sister.DEAFFILIATED, 2020)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': 'all'})

    # Should redirect to event details page
    expected_redirect = reverse('attendance:event_details', args=(event.id,))
    self.assertRedirects(response, expected_redirect)
    # Event should be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, True)
    # Sisters 1, 4, 5, and 6 should be required to attend
    self.assertEqual(len(event_new.sisters_required.all()),  4)
    self.assertEqual(sister1 in event_new.sisters_required.all(), True)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), True)
    self.assertEqual(sister5 in event_new.sisters_required.all(), True)
    self.assertEqual(sister6 in event_new.sisters_required.all(), True)
    self.assertEqual(sister10 in event_new.sisters_required.all(), False)

  # Activate an event for only new members
  def test_activate_new_members(self):
    event = create_event("new member meeting", 6, 20)
    superuser = create_and_login_user(self.client, 'bob', 'siewj', True, test_email)

    # Sisters of all statuses and years
    sister1 = create_sister('active2018', Sister.ACTIVE, 2018)
    sister2 = create_sister('alum2015', Sister.ALUM, 2015)
    sister3 = create_sister('abroad2018', Sister.ABROAD, 2018)
    sister4 = create_sister('newmembie2020', Sister.NEW_MEMBER, 2020)
    sister5 = create_sister('prc2017', Sister.PRC, 2017)
    sister6 = create_sister('active2019', Sister.ACTIVE, 2019)
    sister7 = create_sister('newmembie2019', Sister.NEW_MEMBER, 2019)
    sister10 = create_sister('deaffiliated2020', Sister.DEAFFILIATED, 2020)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': 'new_members'})

    # Should redirect to event details page
    expected_redirect = reverse('attendance:event_details', args=(event.id,))
    self.assertRedirects(response, expected_redirect)
    # Event should be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, True)
    # Sisters 4 and 7 should be required to attend
    self.assertEqual(len(event_new.sisters_required.all()),  2)
    self.assertEqual(sister1 in event_new.sisters_required.all(), False)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), True)
    self.assertEqual(sister5 in event_new.sisters_required.all(), False)
    self.assertEqual(sister6 in event_new.sisters_required.all(), False)
    self.assertEqual(sister7 in event_new.sisters_required.all(), True)
    self.assertEqual(sister10 in event_new.sisters_required.all(), False)

  # Activate an event for a specific class year
  def test_activate_class_year(self):
    event = create_event("2018s fireside", 6, 20)
    superuser = create_and_login_user(self.client, 'bob', 'siewj', True, test_email)

    # Sisters of all statuses and years
    sister1 = create_sister('active2018', Sister.ACTIVE, 2018)
    sister2 = create_sister('alum2015', Sister.ALUM, 2015)
    sister3 = create_sister('abroad2018', Sister.ABROAD, 2018)
    sister4 = create_sister('newmembie2020', Sister.NEW_MEMBER, 2020)
    sister5 = create_sister('prc2017', Sister.PRC, 2017)
    sister6 = create_sister('active2019', Sister.ACTIVE, 2019)
    sister7 = create_sister('newmembie2019', Sister.NEW_MEMBER, 2019)
    sister8 = create_sister('newmembie2018', Sister.NEW_MEMBER, 2018)
    sister9 = create_sister('alum2018', Sister.ALUM, 2018)
    sister10 = create_sister('deaffiliated2020', Sister.DEAFFILIATED, 2020)
    sister11 = create_sister('deaffiliated2018', Sister.DEAFFILIATED, 2018)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': '2018'})

    # Should redirect to event details page
    expected_redirect = reverse('attendance:event_details', args=(event.id,))
    self.assertRedirects(response, expected_redirect)
    # Event should be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, True)
    # Sisters 1 and 8should be required to attend
    # Abroad and alum don't attend)
    self.assertEqual(len(event_new.sisters_required.all()),  2)
    self.assertEqual(sister1 in event_new.sisters_required.all(), True)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), False)
    self.assertEqual(sister5 in event_new.sisters_required.all(), False)
    self.assertEqual(sister6 in event_new.sisters_required.all(), False)
    self.assertEqual(sister7 in event_new.sisters_required.all(), False)
    self.assertEqual(sister8 in event_new.sisters_required.all(), True)
    self.assertEqual(sister9 in event_new.sisters_required.all(), False)
    self.assertEqual(sister10 in event_new.sisters_required.all(), False)
    self.assertEqual(sister11 in event_new.sisters_required.all(), False)

  # Activate an event for a class year that doesn't have anyone in it
  def test_activate_class_year_no_one_in_it(self):
    event = create_event("2021s fireside", 3, 30)
    superuser = create_and_login_user(self.client, 'bob', 'siewj', True, test_email)

    # Sisters of all statuses and years
    sister1 = create_sister('active2018', Sister.ACTIVE, 2018)
    sister2 = create_sister('alum2015', Sister.ALUM, 2015)
    sister3 = create_sister('abroad2018', Sister.ABROAD, 2018)
    sister4 = create_sister('newmembie2020', Sister.NEW_MEMBER, 2020)
    sister5 = create_sister('prc2017', Sister.PRC, 2017)
    sister10 = create_sister('deaffiliated2020', Sister.DEAFFILIATED, 2020)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': '2021'})

    # Should redirect to event details page
    expected_redirect = reverse('attendance:event_details', args=(event.id,))
    self.assertRedirects(response, expected_redirect)
    # Event should be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, True)
    self.assertEqual(len(event_new.sisters_required.all()),  0)
    self.assertEqual(sister1 in event_new.sisters_required.all(), False)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), False)
    self.assertEqual(sister5 in event_new.sisters_required.all(), False)
    self.assertEqual(sister10 in event_new.sisters_required.all(), False)
