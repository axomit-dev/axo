from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible

from django.db import models
from general.models import Sister
from django.forms import ModelForm

@python_2_unicode_compatible
# An elected position in the sorority.
class Office(models.Model):
  title = models.CharField(max_length=100)
  description = models.TextField(blank=True)

  is_exec = models.BooleanField(default=False)
  # Used to determine whether multiple people can run for the position
  is_committee = models.BooleanField(default=False)

  ALL_CLASSES = 0
  FRESHMAN = 1
  SOPHOMORE = 2
  JUNIOR = 3
  SENIOR = 4
  CLASSES = (
    (ALL_CLASSES, 'All Classes'),
    (FRESHMAN, 'Freshman'),
    (SOPHOMORE, 'Sophomore'),
    (JUNIOR, 'Junior'),
    (SENIOR, 'Senior'),
  )
  # For positions that can only be held by a certain class year (e.g. CRSB Rep)
  eligible_class = models.IntegerField(choices=CLASSES, default=ALL_CLASSES)
  # Note that the settings.py file determines which class year is associated
  # with which class (i.e. the 2020s are freshmen).

  # Non-execs report to their exec officer.
  # Exec officers report to no one.
  # TODO: Figure out how to make it be blank.
  #reports_to = models.ForeignKey('Office', default=0)

  def __str__(self):
    return self.title

# An indication of a sister's interest in an office
class OfficeInterest(models.Model):
  sister = models.ForeignKey(Sister)
  office = models.ForeignKey(Office)

  YES = 0
  MAYBE = 1
  NO = 2
  INTEREST_LEVELS = (
    (YES, 'Yes'),
    (NO, 'No'),
    (MAYBE, 'Maybe'),
  )
  interest = models.IntegerField(choices=INTEREST_LEVELS)

  class Meta:
    # There should only be one entry for a sister-office pair
    unique_together = ('sister', 'office')
    # Order by office then by interest, Yes first and No last
    ordering = ['office', 'interest']

class Loi(models.Model):
  office = models.ForeignKey(Office)
  # LOIs for a committee position can have more than 1 sisters
  sisters = models.ManyToManyField(Sister)
  loi_text = models.TextField()

  # Used to display the sisters for the LOI in the admin view
  def names_of_sisters(self):
    total = ''
    for sister in self.sisters.all():
      total = total + ', ' + sister.__str__()
    return total

  class Meta:
    # Order by office
    ordering = ['office']

# Create a form that mirrors the LOI model
# so it can be used in the view really easily
class LoiForm(ModelForm):
  def __init__(self, exec_election, *args, **kwargs):
    super(LoiForm, self).__init__(*args, **kwargs);

    # Only allow positions for the correct type of election
    self.fields['office'].queryset = Office.objects.filter(is_exec=exec_election)

    # Only allow active sisters / new members to submit LOIs
    self.fields['sisters'].queryset = Sister.objects.filter(status__in=[Sister.NEW_MEMBER, Sister.ACTIVE])

  class Meta:
    model = Loi
    fields = ['office', 'sisters', 'loi_text']

