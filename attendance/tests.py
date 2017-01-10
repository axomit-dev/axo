import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, Sister


def create_event(event_name, days, is_mandatory=False, is_activated=False):
  """
  Helper method to create an event.
  days is the number of days offset from 2/5/2017 at 5am that the event occurs.
  A negative number means the event was in the past.
  Returns the new event.
  """
  # 5AM because of our timezone relative to UTC.
  time = datetime.datetime(2017, 2, 5) + datetime.timedelta(days=days)
  return Event.objects.create(name=event_name, date=time, is_mandatory=is_mandatory, is_activated=is_activated)



class EventsAllViewTests(TestCase):
  def test_all_events_view_with_no_events(self):
    """
    If no events exist, an aappropriate message should be displayed.
    """
    response = self.client.get(reverse('attendance:events'))
    self.assertContains(response, "No events are available.")
    self.assertQuerysetEqual(response.context['events'], [])

  def test_all_events_view_with_one_inactive_event(self):
    """
    The inactive event should be displayed.
    """
    create_event(event_name="Hello", days=2)
    response = self.client.get(reverse('attendance:events'))
    self.assertContains(response, "Activate Now") # Activation button
    self.assertContains(response, "Hello")

  def test_all_events_view_with_two_events(self):
    """
    Events should be displayed with those most in the past at the bottom.
    """
    create_event(event_name="Older", days=-1)
    create_event(event_name="Newer", days=1)
    response = self.client.get(reverse('attendance:events'))
    self.assertQuerysetEqual(
        response.context['events'],
        ['<Event: Newer | Monday, February 06 2017 at 05:00AM>', '<Event: Older | Saturday, February 04 2017 at 05:00AM>']
    )
