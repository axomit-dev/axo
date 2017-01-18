import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Event
from . import views
from general.models import Sister

temp_email = 'axo.mit.attendance@gmail.com'


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
  print(result)
  return User.objects.get(username=username)

##########################
##### ACTIVATE TESTS #####
##########################

class ActivateTests(TestCase):
  # Possible activate_groups: 'all', 'new_members', and a year in string form
  
  # Activate an event without any sisters
  def test_activate_simple(self):
    # Create database objects
    event = create_event("new_event", 1, 10)
    user = create_and_login_user(self.client, 'joe', 'bro', True, temp_email)

    # Make POST request
    post_url = reverse('attendance:activate', kwargs={'event_id': event.id})
    response = self.client.post(post_url, {'activate_group': 'all'})

    # Should redirect to event details page
    expected_redirect = reverse('attendance:event_details', args=(event.id,))
    self.assertRedirects(response, expected_redirect)
    # Event should be activated
    event_new = Event.objects.get(id=event.id)
    self.assertEqual(event_new.is_activated, True)

  # Activate an event when not logged in
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

  # Should redirect to the login page, saying insufficient permissions?
  # Event shouldn't be activated
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

  # Should give 404
  def test_activate_invalid_event(self):
    self.assertEqual(True, True)

  # Idk what this should do
  def test_activate_invalid_group(self):
    self.assertEqual(True, True)

  # Activate an event that is for everyone
  def test_activate_all(self):
    self.assertEqual(True, True)

  # Activate an event for only new members
  def test_activate_new_members(self):
    self.assertEqual(True, True)

  # Activate an event for a specific class year
  def test_activate_class_year(self):
    self.assertEqual(True, True)

  # Activate an event for a class year that doesn't have anyone in it
  def test_activate_class_year_no_one_in_it(self):
    self.assertEqual(True, True)
