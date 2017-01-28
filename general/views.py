from django.shortcuts import render

from .models import Sister

##########################
##### HELPER METHODS #####
##########################

# Returns dictionary with user and sister if someone is logged in.
def get_context(request):
  context = {}
  context['user'] = request.user
  if request.user.is_authenticated():
    try:
      context['sister'] = Sister.objects.get(user=request.user)
    except:
      pass
  return context

# Returns the current sister logged in, if there is one.
def get_sister(request):
  context = get_context(request)
  if context.get('sister'):
    return context['sister']
  else:
    return None


def index(request):
  return render(request, 'general/index.html', {})

def credits(request):
  return render(request, 'general/credits.html', {})