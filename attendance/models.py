from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Event(models.Model):
  name = models.CharField(max_length=200)
  date = models.DateTimeField()
  isMandatory = models.BooleanField(default=False)

  def __str__(self):
    formatted_date = self.date.strftime("%A, %B %d %Y at %I:%M%p")
    return self.name + " at " + formatted_date

