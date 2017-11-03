from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

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
  loi_results_open = models.BooleanField(default=False)
  slating_open = models.BooleanField(default=False)
  voting_open = models.BooleanField(default=False)

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
    ordering = ['office', 'interest', 'sister']

class Loi(models.Model):
  office = models.ForeignKey(Office)
  # LOIs for a committee position can have more than 1 sisters
  sisters = models.ManyToManyField(Sister)
  loi_text = models.TextField()

  # Used to display the sisters for the LOI in the admin view
  def names_of_sisters(self):
    total = ''
    for sister in self.sisters.all():
      total = total + sister.__str__() + ', '
    return total[:-2] # Remove last comma and space

  def __str__(self):
    return 'Office: ' + self.office.__str__() + '. ' + \
           'Sister(s): ' + self.names_of_sisters() + '. ' + \
           'LOI: ' + self.loi_text[:50]
           # Only show first 50 characters of LOI

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

  def clean(self):
    cleaned_data = super(LoiForm, self).clean()
    office = cleaned_data.get('office')
    sisters = cleaned_data.get('sisters')

    # Non-committee offices cannot have > 1 sister on an LOI
    if (not office.is_committee and sisters.count() > 1):    
      self.add_error(
        'sisters',
        ValidationError(_('Only one sister can run for this office.'))
      )

    # Offices for specific classes should only have LOIs with
    # sisters that are in that class
    if (not office.eligible_class == Office.ALL_CLASSES):
      for sister in sisters:
        if not is_eligible(sister, office):
          self.add_error(
            'sisters',
            ValidationError(_('Only %(eligible_class)ss can run for %(office_title)s. ' + 
              'However, %(sister)s is a %(sister_year)s.'),
              params={'eligible_class': office.get_eligible_class_display(),
                      'office_title': office.title,
                      'sister': sister,
                      'sister_year': sister.class_year}
                      # TODO: Convert class year into a word? (e.g. 2018 -> senior)
            )
          )


  # TODO: Make sure there aren't two LOIs like "caitlin for soph semi"
  #   and "caitlin and rebecca for soph semi"
  # TODO: Make sure that any LOI you submit has to include yourself

# A sister's slate for a specific position.
class Slate(models.Model):
  # The sister casting this slate
  sister = models.ForeignKey(Sister)

  # Office that the slate is for
  office = models.ForeignKey(Office)

  # Votes are null if they're a vote for 'abstain'

  # First choice for candidate
  vote_1 = models.ForeignKey(Loi, null=True, related_name='vote_1')

  # Second choice for candidate
  vote_2 = models.ForeignKey(Loi, null=True, related_name='vote_2')

  class Meta:
    # There should only be one entry for a sister-office pair
    # (you can only slate for a position once)
    unique_together = ('sister', 'office')
    # TODO: Assert that vote_1 and vote_2 are for self.office

# A final vote for an office
class FinalVote(models.Model):
  # Office that the vote is for
  office = models.ForeignKey(Office)

  # Type of vote
  ABSTAIN = 0
  I_DONT_KNOW = 1
  PERSON = 2 # If they voted for a specific person
  VOTE_TYPES = (
    (ABSTAIN, 'Abstain'),
    (I_DONT_KNOW, 'I don\'t know'),
    (PERSON, 'Person'),
  )
  vote_type = models.IntegerField(choices=VOTE_TYPES)

  # Their vote
  vote = models.ForeignKey(Loi, null=True)

  # TODO: Assert that vote is blank if they chose abstain or I don't know

# A sister who submitted a final vote in an election
class FinalVoteParticipant(models.Model):
  # The sister that submitted a final vote
  sister = models.ForeignKey(Sister)

  # TODO: Prevent the deletion of a single FinalVoteParticipant
  #   so you can only delete them all at once.
  #   Do this to prevent selectively removing participants
  #   so they can vote multiple times.
  #   Also, should probably remove from the admin interface.

# A setting for which candidates can be voted on
# in a final election
class VotingSetting(models.Model):
  # Office that this vote setting is for
  office = models.ForeignKey(Office)

  # First candidate
  candidate_1 = models.ForeignKey(Loi, null=True, related_name='candidate_1')

  # Second candidate
  candidate_2 = models.ForeignKey(Loi, null=True, related_name='candidate_2')


##########################
##### HELPER METHODS #####
##########################


# Returns the current election settings.
def get_election_settings():
  # There should always be exactly one ElectionSettings instance.
  return ElectionSettings.objects.all().first()


# Returns true if the sister is eligible to run / vote
# for the given office.
def is_eligible(sister, office):
  if office.eligible_class == Office.ALL_CLASSES:
    return True
  else:
    # TODO: Better way to do this?
    if office.eligible_class == Office.FRESHMAN:
      class_year = get_election_settings().senior_class_year + 3
    elif office.eligible_class == Office.SOPHOMORE:
      class_year = get_election_settings().senior_class_year + 2
    elif office.eligible_class == Office.JUNIOR:
      class_year = get_election_settings().senior_class_year + 1
    else: # office.eligible_class == Office.SENIOR:
      class_year = get_election_settings().senior_class_year

    return sister.class_year == class_year