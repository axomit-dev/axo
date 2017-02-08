from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User

@python_2_unicode_compatible
class Sister(models.Model):
  ACTIVE = 0
  ALUM = 1
  NEW_MEMBER = 2
  # Deleted PRC status
  ABROAD = 4
  DEAFFILIATED = 5
  STATUS = (
    (ACTIVE, 'Active'),
    (ALUM, 'Alum'),
    (NEW_MEMBER, 'New Member'),
    (ABROAD, 'Abroad'),
    (DEAFFILIATED, 'Deaffiliated'),
  )

  user = models.OneToOneField(User, on_delete=models.CASCADE)
  status = models.IntegerField(choices=STATUS)
  class_year = models.IntegerField()

  class Meta:
    # Order by first name then last name
    ordering = ['user__first_name', 'user__last_name']

  def __str__(self):
    # TODO: Make first_name, last_name required for Users somehow
    return "%s %s" % (self.user.first_name, self.user.last_name)






