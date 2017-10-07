from django.contrib import admin

from .models import ElectionSettings, Office, OfficeInterest, Loi

class ElectionSettingsAdmin(admin.ModelAdmin):
  list_display = ('exec_election', 'ois_open', 'ois_results_open', 'loi_open', 'slating_open', 'senior_class_year')

class OfficeAdmin(admin.ModelAdmin):
  list_display = ('title', 'is_exec', 'eligible_class')

class OfficeInterestAdmin(admin.ModelAdmin):
  list_display = ('sister', 'office', 'interest')

class LoiAdmin(admin.ModelAdmin):
  list_display = ('office', 'names_of_sisters', 'loi_text')

admin.site.register(ElectionSettings, ElectionSettingsAdmin)
admin.site.register(Office, OfficeAdmin)
admin.site.register(OfficeInterest, OfficeInterestAdmin)
admin.site.register(Loi, LoiAdmin)
