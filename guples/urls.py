from reroute import handler404, handler500, patterns, url, include
from reroute.verbs import verb_url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$',               'guples.views.home'),

    # Heroku-specific routes
	verb_url('POST',         r'^heroku/resources$',                        'guples.views.heroku_provision'),
	verb_url('DELETE',       r'^heroku/resources/(?P<id>[0-9].*)$',        'guples.views.heroku_deprovision'),
	verb_url('PUT',          r'^heroku/resources/(?P<id>[0-9].*)$',        'guples.views.heroku_planchange'),
	verb_url('GET',          r'^heroku/resources/(?P<id>[0-9].*)$',        'guples.views.heroku_sso_for_resource'),
	verb_url('POST',         r'^sso/login$',                               'guples.views.heroku_sso'),	
	verb_url('GET',          r'^heroku/ssolanding$',                       'guples.views.heroku_sso_landing'),
)
