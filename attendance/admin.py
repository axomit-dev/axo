from django.contrib import admin

from .models import Event, Semester, Excuse

class EventAdmin(admin.ModelAdmin):
  fieldsets = [
    (None, {'fields': ['name', 'date', 'is_mandatory', 'points', 'semester', 'sisters_excused', 'sisters_freebied']})
  ]
  list_display = ('name', 'date', 'is_mandatory', 'points', 'semester')

  list_filter = ['semester', 'date', 'points', 'is_mandatory']
  search_fields = ['name']


admin.site.register(Event, EventAdmin)
admin.site.register(Semester)
admin.site.register(Excuse)
