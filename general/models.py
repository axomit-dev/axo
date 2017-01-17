from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User

@python_2_unicode_compatible
class Sister(models.Model):
  ACTIVE = 0
  ALUM = 1
  NEW_MEMBER = 2
  PRC = 3
  ABROAD = 4
  STATUS = (
    (ACTIVE, 'Active'),
    (ALUM, 'Alum'),
    (NEW_MEMBER, 'New Member'),
    (PRC, 'PRC'),
    (ABROAD, 'Abroad')
  )

  user = models.OneToOneField(User, on_delete=models.CASCADE)
  status = models.IntegerField(choices=STATUS)
  class_year = models.IntegerField()


  def __str__(self):
    return self.user.username
    # TODO: Make first_name, last_name required for Users somehow
    #return "%s %s" % (self.user.first_name, self.user.last_name)
