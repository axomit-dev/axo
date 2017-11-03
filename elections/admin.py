from django.contrib import admin

from .models import ElectionSettings, Office, OfficeInterest, Loi, Slate, FinalVote, FinalVoteParticipant, VotingSetting

class OfficeAdmin(admin.ModelAdmin):
  list_display = ('title', 'is_exec', 'eligible_class')

class OfficeInterestAdmin(admin.ModelAdmin):
  list_display = ('sister', 'office', 'interest')

class LoiAdmin(admin.ModelAdmin):
  list_display = ('office', 'names_of_sisters', 'loi_text')

admin.site.register(ElectionSettings)
admin.site.register(Office, OfficeAdmin)
admin.site.register(OfficeInterest, OfficeInterestAdmin)
admin.site.register(Loi, LoiAdmin)
admin.site.register(Slate)
# TODO: Give better display of FinalVote + FinalVoteParticipant
admin.site.register(FinalVote)
admin.site.register(FinalVoteParticipant)
admin.site.register(VotingSetting)