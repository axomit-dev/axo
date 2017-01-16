from django.contrib import admin

from .models import Event, Sister

class EventAdmin(admin.ModelAdmin):
  fieldsets = [
    (None, {'fields': ['name', 'date', 'is_mandatory', 'points']})
  ]
  list_display = ('name', 'date', 'is_mandatory', 'points')

admin.site.register(Event, EventAdmin)
admin.site.register(Sister)