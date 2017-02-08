from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from general.models import Sister
from django.utils.timezone import localtime


@python_2_unicode_compatible
class Semester(models.Model):
  FALL = 'Fall'
  SPRING = 'Spring'
  TERM = (
    (FALL, 'Fall'),
    (SPRING, 'Spring'),
  )
  term = models.CharField(choices=TERM, max_length=6)
  year = models.IntegerField()

  class Meta:
    # TODO: test this ordering
    # Ordering latest semester to earliest
    # Latest year first, so sort by year descending (with - sign).
    # Fall alphabetically comes before spring and fall is later
    # than spring, so order by term ascending (without - sign).
    ordering = ['-year', 'term']

  def __str__(self):
    return self.term + " " + str(self.year)

@python_2_unicode_compatible
class Event(models.Model):
  name = models.CharField(max_length=200)
  date = models.DateTimeField()
  is_mandatory = models.BooleanField(default=False)
  is_activated = models.BooleanField(default=False)
  semester = models.ForeignKey(Semester)

  sisters_required = models.ManyToManyField(Sister, blank=True, related_name='sisters_required')
  sisters_attended = models.ManyToManyField(Sister, blank=True, related_name='sisters_attended')
  sisters_excused = models.ManyToManyField(Sister, blank=True, related_name='sisters_excused')
  
  # List of sisters who used their freebie for this event.
  sisters_freebied = models.ManyToManyField(Sister, blank=True, related_name='sisters_freebied')

  points = models.IntegerField()
 
  class Meta:
    ordering = ['-date']

  def __str__(self):
    # Convert date to current timezone
    aware_date = localtime(self.date)
    formatted_date = '{dt:%a} {dt.month}/{dt.day}/{dt.year} at {dt:%I}:{dt:%M}{dt:%p}'.format(dt=aware_date)
    return self.name + " | " + formatted_date


class Excuse(models.Model):
  PENDING = 0
  APPROVED = 1
  DENIED = 2
  STATUS = (
    (PENDING, 'Pending'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied')
  )

  event = models.ForeignKey(Event)
  sister = models.ForeignKey(Sister)
  text = models.CharField(max_length=1000)
  status = models.IntegerField(choices=STATUS, default=PENDING)

  # If true, the user would like to use their freebie for the semester
  # on this event, meaning they get 100% of the points
  # and do not need to attend.
  is_freebie = models.BooleanField(default=False)
