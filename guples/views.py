from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from guples.models import Guple, GupleStore, Plan
from settings import *
import logging
import json
import base64
import hashlib
import time
import datetime
import requests
import HTMLParser

logger = logging.getLogger(__name__)

# ===== VIEW HELPERS =====

def _heroku_nav_header():
	response = requests.get('http://nav.heroku.com/v1/providers/header')
	h = HTMLParser.HTMLParser()
	return h.unescape(response.content)

def _unauthorize_response():
	response = HttpResponse()
	response.status_code = 401
	response['WWW-Authenticate'] = 'Basic realm="%s"' % 'Restricted area'

	return response

def _is_authorized(request):
	if 'HTTP_AUTHORIZATION' not in request.META:
		logger.error("HTTP_AUTHORIZATION not found in META header")
		return False

	auth = request.META['HTTP_AUTHORIZATION'].split()
	if len(auth) != 2:
		logger.error("HTTP_AUTHORIZATION header is not of correct length")
		return False

	if auth[0].lower() != "basic":
		logger.error("Auth type is not basic")
		return False

	uname, passwd = base64.b64decode(auth[1]).split(':')
	logger.info("Username %s" % uname)
	logger.info("Password %s" % passwd)
	if uname != HEROKU_USERNAME or passwd != HEROKU_PASSWORD:
		logger.error("Username and password mismatch")
		return False

	return True

def _json_body(request):
	if request:
		return json.loads(request.body)

	return None

# ===== VIEWS ======

def home(request):
	logger.info("someone visited the home page")
	return HttpResponse('hello world')

@csrf_exempt
def heroku_provision(request):
	if not _is_authorized(request):
		return _unauthorize_response()

	plan_requested = _json_body(request)['plan']
	logger.info("Request plan is %s" % plan_requested)

	plan = Plan.objects.get(name=plan_requested)
	guple_store = GupleStore.objects.create(plan=plan)

	# return resource data
	return HttpResponse(
					json.dumps(
						{
							'id': guple_store.id,
							'config':
								{
									"GUPLES_ACCESS_URL": "http://gupleapp.com/%s" % guple_store.secret_key
								}
						}
					)
				)

@csrf_exempt
def heroku_deprovision(request, id):
	if not _is_authorized(request):
		return _unauthorize_response()

	try:
		guple_store = GupleStore.objects.get(id=id)
	except GupleStore.DoesNotExist:
		return HttpResponse(status=404)
	guple_store.delete()

	return HttpResponse(status=200)

def heroku_planchange(request, id):
	if not _is_authorized(request):
		return _unauthorize_response()

	guple_store = GupleStore.objects.get(id=id)
	requested_plan = Plan.objects.get(name=_json_body(request)['plan'])
	guple_store.plan = requested_plan
	guple_store.save()

	return HttpResponse(status=200)

@csrf_exempt
def _do_sso(request):
	pre_token = request.REQUEST['id'] + ":" + HEROKU_SSO_SALT + ":" + request.REQUEST['timestamp']
	token = hashlib.sha1(pre_token).hexdigest()
	if token != request.REQUEST['token']:
		return HttpResponseServerError(status=403)
	if int(request.REQUEST['timestamp']) < int((time.time() - 2*60)):
		return HttpResponseServerError(status=403)

	try:
		guple_store = GupleStore.objects.get(id=request.REQUEST['id'])
	except GupleStore.DoesNotExist:
		return HttpResponseServerError(status=404)

	response = redirect('/heroku/ssolanding')

	request.session['heroku-nav-data'] = request.REQUEST['nav-data']
	request.session['heroku_sso'] = True
	request.session['email'] = request.REQUEST['email']
	request.session['id'] = request.REQUEST['id']

	response.set_cookie('heroku-nav-data',request.REQUEST['nav-data'])

	return response

def heroku_sso_landing(request):
	if not request.session.get('heroku_sso'):
		return HttpResponse(status=403)

	try:
		guple_store = GupleStore.objects.get(id=request.session.get('id'))
	except GupleStore.DoesNotExist:
		return HttpResponseServerError(status=404)

	return render_to_response(
		'heroku/sso_landing.html',
		{
			'nav_header': _heroku_nav_header(),
			'guple_store': guple_store,
			'email':    request.session.get('email')
		},
		context_instance = RequestContext(request)
	)

def heroku_sso_for_resource(request, id):
	return _do_sso(request)

@csrf_exempt
def heroku_sso(request):
	return _do_sso(request)