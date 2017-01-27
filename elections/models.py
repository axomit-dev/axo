from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.db import models

@python_2_unicode_compatible
class Office(models.Model):
  title = models.CharField(max_length=100)
  description = models.TextField(blank=True)

  is_exec = models.BooleanField(default=False)
  # Used to determine whether multiple people can run for the position
  is_committee = models.BooleanField(default=False)

  def __str__(self):
    return self.title