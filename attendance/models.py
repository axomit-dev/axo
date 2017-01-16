from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from general.models import Sister

@python_2_unicode_compatible
class Event(models.Model):
  # Excused absences are worth 75% of the original point value
  VALUE_OF_EXCUSED_ABSENCE = .75

  name = models.CharField(max_length=200)
  date = models.DateTimeField()
  is_mandatory = models.BooleanField(default=False)
  is_activated = models.BooleanField(default=False)
  sisters_required = models.ManyToManyField(Sister, blank=True, related_name='sisters_required')
  sisters_attended = models.ManyToManyField(Sister, blank=True, related_name='sisters_attended')
  sisters_excused = models.ManyToManyField(Sister, blank=True, related_name='sisters_excused')

  points = models.IntegerField()
  def __str__(self):
    formatted_date = self.date.strftime("%A, %B %d %Y at %I:%M%p")
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
