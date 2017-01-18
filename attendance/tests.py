import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Event
from . import views
from general.models import Sister

test_email = 'axo.mit.attendance@gmail.com'

##########################
##### HELPER METHODS #####
##########################

def create_event(event_name, days, points, is_mandatory=False, is_activated=False):
  """
  Helper method to create an event.
  days is the number of days offset from 2/5/2017 at 5am that the event occurs.
  A negative number means the event was in the past.
  Returns the new event.
  """
  # 5AM because of our timezone relative to UTC.
  time = timezone.now() + datetime.timedelta(days=days)
  return Event.objects.create(name=event_name, date=time, points=points, is_mandatory=is_mandatory, is_activated=is_activated)


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

##########################
##### ACTIVATE TESTS #####
##########################

# TODO: Test the actual HTML that's returned?
class ActivateTests(TestCase):
  # Possible activate_groups: 'all', 'new_members', and a year in string form
  
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
    self.assertEqual(sister1 in event_new.sisters_required.all(), True)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), True)
    self.assertEqual(sister5 in event_new.sisters_required.all(), True)
    self.assertEqual(sister6 in event_new.sisters_required.all(), True)

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
    self.assertEqual(sister1 in event_new.sisters_required.all(), False)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), True)
    self.assertEqual(sister5 in event_new.sisters_required.all(), False)
    self.assertEqual(sister6 in event_new.sisters_required.all(), False)
    self.assertEqual(sister7 in event_new.sisters_required.all(), True)

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
    self.assertEqual(sister1 in event_new.sisters_required.all(), True)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), False)
    self.assertEqual(sister5 in event_new.sisters_required.all(), False)
    self.assertEqual(sister6 in event_new.sisters_required.all(), False)
    self.assertEqual(sister7 in event_new.sisters_required.all(), False)
    self.assertEqual(sister8 in event_new.sisters_required.all(), True)
    self.assertEqual(sister9 in event_new.sisters_required.all(), False)

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

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': '2021'})

    # Should redirect to event details page
    expected_redirect = reverse('attendance:event_details', args=(event.id,))
    self.assertRedirects(response, expected_redirect)
    # Event should be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, True)
    # Sisters 1 and 8should be required to attend
    # Abroad and alum don't attend)
    self.assertEqual(sister1 in event_new.sisters_required.all(), False)
    self.assertEqual(sister2 in event_new.sisters_required.all(), False)
    self.assertEqual(sister3 in event_new.sisters_required.all(), False)
    self.assertEqual(sister4 in event_new.sisters_required.all(), False)
    self.assertEqual(sister5 in event_new.sisters_required.all(), False)
