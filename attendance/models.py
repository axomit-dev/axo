from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from general.models import Sister


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
  # Excused absences are worth 75% of the original point value
  VALUE_OF_EXCUSED_ABSENCE = .75

  name = models.CharField(max_length=200)
  date = models.DateTimeField()
  is_mandatory = models.BooleanField(default=False)
  is_activated = models.BooleanField(default=False)
  semester = models.ForeignKey(Semester)

  sisters_required = models.ManyToManyField(Sister, blank=True, related_name='sisters_required')
  sisters_attended = models.ManyToManyField(Sister, blank=True, related_name='sisters_attended')
  sisters_excused = models.ManyToManyField(Sister, blank=True, related_name='sisters_excused')

  points = models.IntegerField()
 
  class Meta:
    ordering = ['-date']

  def __str__(self):
    # Example display of the formatted date:
    # Sunday 1/19/17 at 6:30pm
    formatted_date = '{dt:%a} {dt.month}/{dt.day}/{dt.year} at {dt:%I}:{dt:%M}{dt:%p}'.format(dt=self.date)
    #formatted_date = self.date.strftime("%a %m/%d/%y at %I:%M%p")
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
