from django.contrib import admin

from .models import ElectionSettings, Office, OfficeInterest, Loi

class OfficeInterestAdmin(admin.ModelAdmin):
  list_display = ('sister', 'office', 'interest')

class LoiAdmin(admin.ModelAdmin):
  list_display = ('office', 'names_of_sisters', 'loi_text')

admin.site.register(ElectionSettings)
admin.site.register(Office)
admin.site.register(OfficeInterest, OfficeInterestAdmin)
admin.site.register(Loi, LoiAdmin)
