from django.contrib import admin

from .models import Office, OfficeInterest, Loi

class LoiAdmin(admin.ModelAdmin):
  list_display = ('office', 'names_of_sisters', 'loi_text')

admin.site.register(Office)
admin.site.register(OfficeInterest)
admin.site.register(Loi, LoiAdmin)
