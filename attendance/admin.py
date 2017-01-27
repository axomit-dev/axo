from django.contrib import admin

from .models import Event, Semester

class EventAdmin(admin.ModelAdmin):
  fieldsets = [
    (None, {'fields': ['name', 'date', 'is_mandatory', 'points', 'semester']})
  ]
  list_display = ('name', 'date', 'is_mandatory', 'points', 'semester')

  list_filter = ['semester', 'date', 'points', 'is_mandatory']
  search_fields = ['name']


admin.site.register(Event, EventAdmin)
admin.site.register(Semester)