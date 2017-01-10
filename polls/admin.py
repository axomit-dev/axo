from django.contrib import admin

# Register your models here.
from .models import Question, Choice

class ChoiceInline(admin.TabularInline):
  model = Choice
  extra = 3


class QuestionAdmin(admin.ModelAdmin):
  
  fieldsets = [
    (None, {'fields': ['question_text']}),
    ('Date information', {'fields': ['pub_date']}),
  ]
  inlines = [ChoiceInline]
  # This says: Choice objects are edited on the Question admin page.
  # By default, provide enough fields for 3 choices.

  list_display = ('question_text', 'pub_date', 'was_published_recently')
  list_filter = ['pub_date']
  search_fields = ['question_text']



  #field = ['pub_date', 'question_text']
  # Makes the publication date come before the question field

admin.site.register(Question, QuestionAdmin)

#admin.site.register(Question)
#admin.site.register(Choice)
