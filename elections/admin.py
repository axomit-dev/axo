from django.contrib import admin

from .models import ElectionSettings, Office, OfficeInterest, Loi

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
