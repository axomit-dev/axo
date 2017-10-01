from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError

from django.db import models
from general.models import Sister
from django.forms import ModelForm

# Describes which part of the elections process is open.
# There should be only one instance of election settings
class ElectionSettings(models.Model):
  # Whether the current election is for exec (true) or non-exec (false).
  exec_election = models.BooleanField(default=False)
  ois_open = models.BooleanField(default=False)
  ois_results_open = models.BooleanField(default=False)
  loi_open = models.BooleanField(default=False)
  slating_open = models.BooleanField(default=False)

  # senior_class_year is equal to the class year of the current seniors.
  # It is used for determining who can vote for what positions
  # in elections-related items.
  # This must be changed each fall.
  senior_class_year = models.IntegerField(default=2018)

  # Override save to ensure that there's only one instance of ElectionSettings
  # Reference: https://stackoverflow.com/questions/39412968/allow-only-one-instance-of-a-model-in-django
  def save(self, *args, **kwargs):
    if ElectionSettings.objects.exists() and not self.pk:
      raise ValidationError('There is can be only one ElectionSettings instance')
    return super(ElectionSettings, self).save(*args, **kwargs)


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

# A sister's slate for a specific position.
class Slate(models.Model):
  # The sister casting this slate
  sister = models.ForeignKey(Sister)

  # Office that the slate is for
  office = models.ForeignKey(Office)

  # First choice for candidate
  vote_1 = models.ForeignKey(Loi, related_name='vote_1')

  # Second choice for candidate
  vote_2 = models.ForeignKey(Loi, related_name='vote_2')

  class Meta:
    # There should only be one entry for a sister-office pair
    # (you can only slate for a position once)
    unique_together = ('sister', 'office')
    # TODO: Assert that vote_1 and vote_2 are for self.office
