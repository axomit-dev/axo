from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from general.models import Sister

@python_2_unicode_compatible
class Office(models.Model):
  title = models.CharField(max_length=100)
  description = models.TextField(blank=True)

  is_exec = models.BooleanField(default=False)
  # Used to determine whether multiple people can run for the position
  is_committee = models.BooleanField(default=False)

  def __str__(self):
    return self.title

class OfficeInterest(models.Model):
  # Used to indicate a a sister's interest in an office
  sister = models.ForeignKey(Sister)
  office = models.ForeignKey(Office)

  YES = 'Yes'
  NO = 'No'
  MAYBE = 'Maybe'
  INTEREST_LEVELS = (
    (YES, 'Yes'),
    (NO, 'No'),
    (MAYBE, 'Maybe'),
  )
  interest = models.CharField(choices=INTEREST_LEVELS, max_length=5)