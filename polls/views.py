import re, hashlib, random, json, csv, sys
from datetime import datetime, timedelta, tzinfo
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.core.validators import validate_email
from django.db.models import ProtectedError
from django.forms import ValidationError
from django.forms.models import modelformset_factory, inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError
from django.views.defaults import page_not_found, permission_denied, bad_request
from itertools import chain
from polls import models
from polls.includes import forms, email_messages
from pprint import pprint


#################################################
#### PASO DE MENSAJES Y PARAMETROS POR CACHE ####
#################################################

# Crea un mensaje que se mostrara en la siguiente pagina
def set_cache_message(user, msg_type, msg):

	if not user.is_authenticated():
		return

	cache = caches['default']

	if (msg_type == 'error'):
		key = 'error_msg'
	elif (msg_type == 'warning'):
		key = 'warning_msg'
	elif (msg_type == 'success'):
		key = 'success_msg'
	else:
		key = 'info_msg'

	key = hashlib.sha256(('%d_%s' % (user.pk, key)).encode('utf-8')).hexdigest()
	cache.set(key, msg)

# Lee el contenido de las variables de mensaje si existen.
def caches_messages(user):

	if not user.is_authenticated():
		return

	cache = caches['default']

	# Construyo las claves
	error_key = hashlib.sha256(("%d_error_msg" % user.pk).encode('utf-8')).hexdigest()
	warning_key = hashlib.sha256(("%d_warning_msg" % user.pk).encode('utf-8')).hexdigest()
	success_key = hashlib.sha256(("%d_success_msg" % user.pk).encode('utf-8')).hexdigest()
	info_key = hashlib.sha256(("%d_info_msg" % user.pk).encode('utf-8')).hexdigest()

	# Recojo los mensajes
	error_msg = cache.get(error_key, None);
	warning_msg = cache.get(warning_key, None);
	success_msg = cache.get(success_key, None);
	info_msg = cache.get(info_key, None);

	# Limpio las variables
	cache.set(error_key, None);
	cache.set(warning_key, None);
	cache.set(success_key, None);
	cache.set(info_key, None);

	return error_msg, warning_msg, success_msg, info_msg

def set_cache_param(user, name, value):

	if not user.is_authenticated():
		return

	cache = caches['default']

	key = hashlib.sha256(('%d_%s' % (user.pk, name)).encode('utf-8')).hexdigest()
	cache.set(key, value)

def caches_param(user, name):

	if not user.is_authenticated():
		return

	cache = caches['default']

	key = hashlib.sha256(('%d_%s' % (user.pk, name)).encode('utf-8')).hexdigest()
	param = cache.get(key, None)
	cache.set(key, None)

	return param

#################################################
#################################################


def login_view(request):
	login_active = "active"
	login_form = forms.LoginForm()
	reg_form = forms.RegisterForm()
	js_actions = "$('#registerForm').modal('hide')"
	error_msg = ''
	register_error = ''
	info_msg = ''

	if request.user is not None and request.user.is_active:
		try:
			redir = request.GET['next'];
		except 	MultiValueDictKeyError:
			redir = '/polls/home/';

		return HttpResponseRedirect(redir)


	if (request.method == 'POST'):
		if (request.POST['wichform'] == 'registration'):
			reg_form = forms.RegisterForm(request.POST)
			if reg_form.is_valid():
				password = request.POST['password']
				first_name = request.POST['first_name']
				last_name = request.POST['last_name']
				email = request.POST['email']

				new_user = User.objects.create_user(username=email, password=password, first_name=first_name, last_name=last_name, email=email)
				new_user.is_active = False
				new_user.save()

				# Send activation email
				salt = hashlib.sha256(str(random.getrandbits(256)).encode('utf-8')).hexdigest()[:5]
				activation_key = hashlib.sha256((salt+email).encode('utf-8')).hexdigest()
				key_expires = datetime.now() + timedelta(2)

				new_user_profile = models.UserProfile(user=new_user, activation_key=activation_key, key_expires=key_expires)
				new_user_profile.save()
				new_user_profile.send_activation_email()

				reg_form = forms.RegisterForm()
				info_msg = "Thank you for your registration. You will now receive an activation email. Please activate your account within the next 48 hours."
			else:
				js_actions = "$('#registerForm').modal('show')"
		else:
			login_form = forms.LoginForm(request.POST)
			email = request.POST['email']
			password = request.POST['password']
			user = authenticate(username=email, password=password)
			if user is not None:
				if user.is_active:
					login(request, user)
					try:
						redir = request.GET['next'];
					except 	MultiValueDictKeyError:
						redir = '/polls/home/';

					return HttpResponseRedirect(redir)
				else:
					info_msg = 'Your user has not been activated yet. If the problem persist, please contact us.'
			else:
				error_msg = 'Wrong username or password. Please try again.'

	return render(
					request,
					'polls/login.html',
					context={
						'login_form': login_form,
						'reg_form': reg_form,
						'error_msg': error_msg,
						'info_msg': info_msg,
						'js_actions': js_actions,
						'login_active': login_active,
						'register_error': register_error
					}
				)

def logout_view(request):
	logout(request)
	return HttpResponseRedirect('/polls/login/')

def activate_account(request, activation_key):
	msg = ''
	user_profile = None
	status = False
	try:
		user_profile = models.UserProfile.objects.get(activation_key=activation_key)
		status = user_profile.activate_account(activation_key)
		if not status:
			msg = 'Sorry, your activation link has expired. Please register again.'
		else:
			msg = 'Congratulatins! You have activated your account succesfully. You can now login into BBPolls.'

	except ObjectDoesNotExist:
		msg = "Sorry, your account could not be found or you have already activated your account."

	return render(request, 'polls/activate_account.html',
				{'user_profile':user_profile, 'msg':msg, 'status':status});

@login_required(login_url='/polls/login')
def polls_index(request):
	mypolls_active = 'active'
	js_file = "polls_index.js"

	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True
	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	published_polls = models.Poll.objects.filter(user=request.user, poll_status=models.Poll.ST_PUBLISHED).order_by("publish_date")
	draft_polls = models.Poll.objects.filter(user=request.user, poll_status=models.Poll.ST_DRAFT).order_by("-last_modified")
	archived_polls = models.Poll.objects.filter(user=request.user, poll_status=models.Poll.ST_ARCHIVED).order_by("-archive_date")

	# send_poll_form = forms.SendPollForm()

	error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)
	return render(request, 'polls/polls_index.html',
							{'published_polls':published_polls,
								'username':request.user.username,
								'draft_polls':draft_polls,
								'archived_polls':archived_polls,
								'error_msg':error_msg,
								'warning_msg':warning_msg,
								'success_msg':success_msg,
								'info_msg':info_msg,
								'js_file':js_file,
								'send_poll_form':forms.SendPollForm(),
								'is_pollster':is_pollster,
								'mypolls_active':mypolls_active});


@login_required(login_url='/polls/login')
def send_poll(request, poll_id):
	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True
	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id)
	except ObjectDoesNotExist:
		set_cache_message(request.user, "error", "Sorry! Poll not found")
		return HttpResponseRedirect("/polls/my-polls/")

	# send_poll_form = forms.SendPollForm(request.POST)

	if (request.method == 'POST'):

		emails_text = request.POST["emails"]
		emails = []

		for line_emails in emails_text.splitlines():
			line_emails = line_emails.strip()
			if (',' in line_emails):
				splited_line = line_emails.split(",")
				for e in splited_line:
					e = e.strip()
					if e != "":
						try:
							validate_email(e)
							emails.append(e.strip())
						except ValidationError:
							continue

			elif (';' in line_emails):
				splited_line = line_emails.split(";")
				for e in splited_line:
					e = e.strip()
					if e != "":
						try:
							validate_email(e)
							emails.append(e.strip())
						except ValidationError:
							continue

			elif (' ' in line_emails):
				splited_line = line_emails.split(" ")
				for e in splited_line:
					e = e.strip()
					if e != "":
						try:
							validate_email(e)
							emails.append(e.strip())
						except ValidationError:
							continue

			elif(line_emails != ""):
				try:
					validate_email(line_emails)
					emails.append(line_emails.strip())
				except ValidationError:
					continue

		emails = list(set(emails))

		if not emails:
			set_cache_message(request.user, "warning", "No emails were found")
		else:
			poll.send_poll(emails)
			set_cache_message(request.user, "success", "Invitations sent!")

	return HttpResponseRedirect("/polls/my-polls/")

@login_required(login_url='/polls/login')
def publish_poll(request, poll_id):
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id)

		if (poll.poll_status == models.Poll.ST_ARCHIVED):
			set_cache_message(request.user, "error", "Sorry! An archived poll cannot be unarchived")
			return HttpResponseRedirect("/polls/my-polls/")
		elif (not poll.is_doable):
			set_cache_message(request.user, "error", "Sorry! Is not possible to publish this poll. At least one question in this poll that cannot be proeprly answered")
			return HttpResponseRedirect("/polls/my-polls/")

	except ObjectDoesNotExist:
		set_cache_message(request.user, "error", "Sorry! Poll not found")
		return HttpResponseRedirect("/polls/my-polls/")

	pprint("PUBLISH Current status: %s" % poll.poll_status, sys.stdout)
	poll.poll_status = models.Poll.ST_PUBLISHED
	poll.publish_date = datetime.now()
	poll.save()
	pprint("PUBLISH Current status: %s" % poll.poll_status, sys.stdout)

	return HttpResponseRedirect('/polls/my-polls/')

@login_required(login_url='/polls/login')
def archive_poll(request, poll_id):
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True
	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id)

		if (poll.poll_status == models.Poll.ST_DRAFT):
			set_cache_message(request.user, "error", "Sorry! Only published polls may be archived")
			return HttpResponseRedirect("/polls/my-polls/")

	except ObjectDoesNotExist:
		set_cache_message(request.user, "error", "Sorry! Poll not found")
		return HttpResponseRedirect("/polls/my-polls/")

	models.Response.objects.filter(poll=poll, is_completed=False).delete()
	pprint("ARCHIVE Current status: %s" % poll.poll_status, sys.stdout)
	poll.poll_status = models.Poll.ST_ARCHIVED
	poll.archive_date = datetime.now()
	poll.save()
	pprint("ARCHIVE Current status: %s" % poll.poll_status, sys.stdout)

	return HttpResponseRedirect('/polls/my-polls/')

@login_required(login_url='/polls/login')
def unpublish_poll(request, poll_id):
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id)

		if (poll.poll_status == models.Poll.ST_ARCHIVED):
			set_cache_message(request.user, "error", "Sorry! An archived poll cannot be unarchived")
			return HttpResponseRedirect("/polls/my-polls/")

	except ObjectDoesNotExist:
		set_cache_message(request.user, "error", "Sorry! Poll not found")
		return HttpResponseRedirect("/polls/my-polls/")

	if (models.Response.objects.filter(poll=poll, is_completed=True)):
		set_cache_message(request.user, "error", "Sorry! This poll has already been answered and cannot be unpublish.")
		return HttpResponseRedirect("/polls/my-polls/")

	models.Response.objects.filter(poll=poll, is_completed=False).delete()
	pprint("UNPUBLISH Current status: %s" % poll.poll_status, sys.stdout)
	poll.poll_status = models.Poll.ST_DRAFT
	poll.save()
	pprint("UNPUBLISH New status: %s" % poll.poll_status, sys.stdout)

	return HttpResponseRedirect('/polls/my-polls/')

@login_required(login_url='/polls/login')
def create_poll(request):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	mypolls_active = 'active'
	js_actions = "$('[data-toggle=\"tooltip\"]').tooltip({html: true})"

	create_form = forms.PollCreateForm(request.POST or None, prefix="create");
	import_form = forms.PollImportForm(request.POST or None, request.FILES or None, prefix="import")

	if(request.method == 'POST'): # Create
		if ('create' in request.POST):
			if create_form.is_valid():
				poll_name = request.POST['create-name'];
				p = models.Poll(name=poll_name, user=request.user)
				p.save();
				return HttpResponseRedirect('/polls/manage-poll/%d/' % p.pk)

		elif ('import' in request.POST): # Import
			if (import_form.is_valid()):
				# Check size
				data = b''
				for chunk in request.FILES['import-import_file'].chunks():
					data+=chunk

				json_data = json.loads(data)
				try:
					poll = models.Poll.import_poll(json_data, request.user)
					return HttpResponseRedirect('/polls/manage-poll/%d/' % poll.pk)
				except ValidationError as ve:
					import_form.errors["import_file"] = [ve.messages[0]]

	return render(request, 'polls/create-poll.html',
								{'create_form':create_form,
									'username':request.user.username,
									'import_form':import_form,
									'js_actions':js_actions,
									'is_pollster':is_pollster,
									'mypolls_active':mypolls_active});

@login_required(login_url='/polls/login')
def manage_poll(request, poll_id):

	mypolls_active = 'active'
	js_file = "manage-poll.js"


	js_actions = "$('[data-toggle=\"tooltip\"]').tooltip({html: true});"

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')


	scroll = caches_param(request.user, "scroll")
	pprint(scroll, sys.stderr)
	if scroll:
		js_actions += "$('body').scrollTop(%s)" % scroll

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		poll_form = forms.PollForm(instance = poll)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "Sorry! The poll you are trying to access does not exist anymore.");
		return HttpResponseRedirect("/polls/my-polls/")

	can_edit = poll.poll_status == models.Poll.ST_DRAFT;

	if not can_edit:
		poll_form.disable()

	question_queryset = models.Question.objects.filter(poll=poll).order_by('order');

	if (request.method == 'POST' and can_edit):
		poll_form = forms.PollForm(request.POST, instance=poll)
		if poll_form.is_valid():
			poll_form.save()
			return HttpResponseRedirect('/polls/my-polls/')

	error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)
	return render(request, 'polls/manage-poll.html',
								{'poll_form':poll_form,
									'username':request.user.username,
									'question_queryset':question_queryset,
									'poll':poll,
									'js_file':js_file,
									'js_actions':js_actions,
									'error_msg':error_msg,
									'warning_msg':warning_msg,
									'success_msg':success_msg,
									'info_msg':info_msg,
									'mypolls_active':mypolls_active,
									'is_pollster':is_pollster,
									'can_edit':can_edit});


@login_required(login_url='/polls/login')
def add_question(request, poll_id):
	mypolls_active = 'active'
	js_actions = "$('[data-toggle=\"tooltip\"]').tooltip({html: true})"

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')


	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "The poll you are trying to create a question within, does not exist anymore.");
		return HttpResponseRedirect("/polls/my-polls/")

	try:
		response = models.Response.objects.get(poll=poll, is_completed=True)
		set_cache_message(request.user, 'error', "Sorry! The poll has been already answered and cannot be edited.");
		return HttpResponseRedirect("/polls/my-polls/")

	except ObjectDoesNotExist:
		pass

	question_form = forms.AddQuestionForm(request.POST or None)
	BaseChoiceFormset = inlineformset_factory(models.Question, models.Choice, form=forms.ChoiceForm, extra=3, can_delete=False)
	choice_formset = BaseChoiceFormset()

	if (request.method == 'POST'):
		if (request.POST['submit'] == 'Save'):
			if question_form.is_valid():
				new_question = question_form.save(commit=False)
				new_question.poll = poll
				new_question.save()
				choice_formset = BaseChoiceFormset(request.POST, instance=new_question)
				if choice_formset.is_valid():
					choice_formset.save()
					set_cache_message(request.user, 'success', 'New question created')
					return HttpResponseRedirect('/polls/manage-poll/%s/' % poll_id)

		elif(request.POST['submit'] == 'Save and add new'):
			if question_form.is_valid():
				new_question = question_form.save(commit=False)
				new_question.poll = poll
				new_question.save()
				choice_formset = BaseChoiceFormset(request.POST, instance=new_question)
				if choice_formset.is_valid():
					choice_formset.save()
					question_form = forms.QuestionForm(None)
					set_cache_message(request.user, 'success', 'New question created')
					return HttpResponseRedirect('/polls/manage-poll/%s/add-question/' % poll_id)

		else:
			more_choices = request.POST['number-choices']
			if not more_choices:
				more_choices=0

			try:
				more_choices = int(more_choices)
				if more_choices < 0:
					more_choices = 0

				BaseChoiceFormset = inlineformset_factory(models.Question, models.Choice, form=forms.ChoiceForm, extra=more_choices+3, can_delete=False)

			except ValueError:
				BaseChoiceFormset = inlineformset_factory(models.Question, models.Choice, form=forms.ChoiceForm, extra=3, can_delete=False)
			choice_formset = BaseChoiceFormset()

	error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)
	return render(request, 'polls/manage-question.html',
								{'question_form':question_form,
									'username':request.user.username,
									'poll':poll, 'choice_formset':choice_formset,
									'question_index':poll.number_questions+1,
									'create_question':True,
									'js_actions':js_actions,
									'error_msg':error_msg,
									'warning_msg':warning_msg,
									'success_msg':success_msg,
									'info_msg':info_msg,
									'is_pollster':is_pollster,
									'mypolls_active':mypolls_active});

@login_required(login_url='/polls/login')
def increase_question_order(request, poll_id, question_id, scroll):
	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	mypolls_active = 'active'
	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		question = models.Question.objects.get(pk=question_id, poll=poll)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "Sorry! The question you are trying to increase order to does not exist anymore");
		return HttpResponseRedirect("/polls/manage-poll/%s/" % poll_id)

	pprint(scroll, sys.stderr)
	if scroll:
		set_cache_param(request.user, "scroll", scroll)

	question.increase_order();
	return HttpResponseRedirect("/polls/manage-poll/%s/" % poll_id);

@login_required(login_url='/polls/login')
def decrease_question_order(request, poll_id, question_id, scroll):
	mypolls_active = 'active'

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		question = models.Question.objects.get(pk=question_id, poll=poll)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "Sorry! The question you are trying to decrease order to does not exist anymore");
		return HttpResponseRedirect("/polls/manage-poll/%s/" % poll_id)

	pprint(scroll, sys.stderr)
	if scroll:
		set_cache_param(request.user, "scroll", scroll)

	question.decrease_order();
	return HttpResponseRedirect('/polls/manage-poll/%s/'% poll_id);

@login_required(login_url='/polls/login')
def manage_question(request, poll_id, question_id):
	mypolls_active = 'active'
	manage_only = 'manage-only'
	js_file = "manage-question.js"
	js_actions = "$('[data-toggle=\"tooltip\"]').tooltip({html: true})"

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		question = models.Question.objects.get(pk=question_id, poll=poll)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "The question you are trying to delete does not exist anymore.")
		return HttpResponseRedirect("/polls/manage-poll/%s/" % poll_id)

	can_edit = poll.poll_status == models.Poll.ST_DRAFT;

	i = 0;
	for q in models.Question.objects.filter(poll=poll):
		i +=1;
		if (q.pk == question.pk):
			break;

	BaseChoiceFormset = inlineformset_factory(models.Question, models.Choice, form=forms.ChoiceForm, extra=0)
	multimedia_sources = models.MultimediaSource.objects.filter(question=question).order_by('media_type')
	choice_formset = BaseChoiceFormset(request.POST or None, instance=question)

	if (request.method == 'POST' and can_edit):
		if (request.POST['submit'] == 'Save'):
			question_form = forms.QuestionForm(request.POST, instance=question)
			if question_form.is_valid():
				question = question_form.save()
				if choice_formset.is_valid():
					choice_formset.save();
					return HttpResponseRedirect('/polls/manage-poll/%s/' % poll_id)
		else:
			more_choices = request.POST['number-choices']
			if not more_choices:
				more_choices=0
			try:
				BaseChoiceFormset = inlineformset_factory(models.Question, models.Choice, form=forms.ChoiceForm, extra=int(more_choices))
			except ValueError:
				BaseChoiceFormset = inlineformset_factory(models.Question, models.Choice, form=forms.ChoiceForm, extra=0)

	question_form = forms.QuestionForm(instance=question)
	choice_formset = BaseChoiceFormset(instance=question)

	if not can_edit:
		question_form.disable()
		for choice_form in choice_formset:
			choice_form.disable()


	video_message = "You have %d video sources available" % question.number_video_srcs
	if (question.number_video_srcs > 0):
		video_class = "alert-success"
	else:
		video_class = "alert-danger"

	audio_message = "You have %d audio sources available" % question.number_audio_srcs
	if (question.number_audio_srcs > 0):
		audio_class = "alert-success"
	else:
		audio_class = "alert-danger"

	image_message = "You have %d image sources available" % question.number_image_srcs
	if (question.number_image_srcs > 0):
		image_class = "alert-success"
	else:
		image_class = "alert-danger"

	iframe_message = "You have %d iframe sources available" % question.number_iframe_srcs
	if (question.number_iframe_srcs > 0):
		iframe_class = "alert-success"
	else:
		iframe_class = "alert-danger"

	error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)
	return render(request, 'polls/manage-question.html',
								{'question_form':question_form,
									'username':request.user.username,
									'poll':poll,
									'question_index':i,
									'question_pk':question_id,
									'choice_formset':choice_formset,
									'multimedia_sources':multimedia_sources,
									'manage_only':manage_only,
									'mypolls_active':mypolls_active,
									'create_question':False,
									'error_msg':error_msg,
									'warning_msg':warning_msg,
									'success_msg':success_msg,
									'info_msg':info_msg,
									'image_message': image_message,
									'image_class': image_class,
									'audio_message': audio_message,
									'audio_class': audio_class,
									'video_message': video_message,
									'video_class': video_class,
									'iframe_message': iframe_message,
									'iframe_class': iframe_class,
									'js_file': js_file,
									'js_actions' : js_actions,
									'is_pollster':is_pollster,
									'can_edit':can_edit});

@login_required(login_url='/polls/login')
def clone_poll(request, poll_id):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		poll.clone()
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "Sorry! The poll you are trying to clone does not exist anymore.")

	return HttpResponseRedirect('/polls/my-polls/')

@login_required(login_url='/polls/login')
def remove_poll(request, poll_id):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		poll.delete()
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "Sorry! The poll you are trying to clone does not exist anymore.")

	except ProtectedError:
		set_cache_message(request.user, 'error', "Sorry! The poll has been already answered and cannot be removed.")

	return HttpResponseRedirect('/polls/my-polls/')

@login_required(login_url='/polls/login')
def remove_question(request, poll_id, question_id):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		question = models.Question.objects.get(pk=question_id, poll=poll)
		question.delete()
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "The question you are trying to delete does not exist anymore.")
		return HttpResponseRedirect('/polls/manage-poll/%s/' % poll_id)

	try:
		response = models.Response.objects.get(poll=poll, is_completed=True)
		set_cache_message(request.user, 'error', "Sorry! The poll have been already answered and cannot be edited.")
		return HttpResponseRedirect('/polls/my-polls/')
	except ObjectDoesNotExist:
		pass

	set_cache_message(request.user, 'success', "Question successfully removed")
	return HttpResponseRedirect('/polls/manage-poll/%s/' % poll.pk)

@login_required(login_url='/polls/login')
def add_multimedia_source(request, poll_id, question_id, source='url'):
	mypolls_active = "active"

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		question = models.Question.objects.get(pk=question_id, poll=poll)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "The question you are trying to delete does not exist anymore.")
		return HttpResponseRedirect('/polls/manage-poll/%s/' % poll_id)

	try:
		response = models.Response.objects.get(poll=poll, is_completed=True)
		set_cache_message(request.user, 'error', "Sorry! The poll has been already answered and cannot be edited.");
		return HttpResponseRedirect("/polls/my-polls/")

	except ObjectDoesNotExist:
		pass

	i = 0;
	for q in models.Question.objects.filter(poll=poll):
		i +=1;
		if (q.pk == question.pk):
			break;

	if (source == 'url'):
		if (request.method  == 'POST'):
			multimedia_form = forms.MultimediaSourceFormURL(request.POST)

			if multimedia_form.is_valid():
				try:
					mmsrc = multimedia_form.save(commit=False)
					mmsrc.question = question
					mmsrc.validate_mime_type()
					mmsrc.save()

					set_cache_message(request.user, 'success', "Multimedia source successfully created")
					return HttpResponseRedirect('/polls/manage-poll/%s/manage-question/%s/' % (poll.pk, question.pk))
				except ValidationError as ve:
					multimedia_form = forms.MultimediaSourceFormURL(request.POST)
					multimedia_form.errors["url_source"] = [ve.messages[0]]
		else:
			multimedia_form = forms.MultimediaSourceFormURL()

	elif (source == 'file'):
		pass
	else:
		pass

	return render(request, 'polls/add-multimedia-source.html',
								{'multimedia_form':multimedia_form,
									'username':request.user.username,
									'poll':poll,
									'question':question,
									'question_index':i,
									'mypolls_active':mypolls_active})

@login_required(login_url='/polls/login')
def remove_multimedia_source(request, poll_id, question_id, mmsrc_id):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		question = models.Question.objects.get(pk=question_id, poll=poll)
		mmsrc = models.MultimediaSource.objects.get(pk=mmsrc_id, question=question)
		mmsrc.delete()
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "The source you are trying to delete does not exist anymore.")
		return HttpResponseRedirect("/polls/manage-poll/%s/manage-question/%s/" % (poll.pk, question.pk))

	set_cache_message(request.user, 'success', "Multimedia source successfully removed")
	return HttpResponseRedirect("/polls/manage-poll/%s/manage-question/%s/" % (poll.pk, question.pk))

def do_survey(request, poll_id, try_poll=False, invitation_key=None):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False

	try:
		poll = models.Poll.objects.get(pk=poll_id)
	except ObjectDoesNotExist:
		if try_poll:
			set_cache_message(request.user, 'error', "Poll not found.")
			return HttpResponseRedirect('/polls/my-polls/')
		else:
			set_cache_message(request.user, 'error', "Poll not found.")
			return HttpResponseRedirect('/polls/home/')

	# Comprobamos que el usuario tenga permisos parar acceder
	if (invitation_key is not None):
		try:
			poll_invitation = models.AnonymousInvitation.objects.get(poll=poll, key=invitation_key)
			anonymous_poll = True

			if (poll_invitation.response is not None and poll_invitation.response.is_completed):
				return HttpResponseRedirect('/polls/login/')

		except ObjectDoesNotExist:
			return HttpResponseRedirect('/polls/login/?next=/polls/do-poll/%d/' % poll.pk)


	elif (request.user.is_authenticated()):
		print("auth user")
		if (poll.access_type != models.Poll.AT_PUBLIC):
			if ((request.user not in poll.allowed_users.all()
			and request.user.groups not in poll.allowed_groups.all())
			and (request.user != poll.user and not try_poll)):

				print("not allowed user")
				set_cache_message(request.user, 'error', "Sorry! You don't have permission to access this poll.")
				return HttpResponseRedirect('/polls/home/')

		anonymous_poll = False;
	else:
		print("neither invitation_key, neither allowed_user")
		return HttpResponseRedirect('/polls/login/?next=%s' % request.path)


	if (poll.randomize_questions):
		questions = models.Question.objects.filter(poll=poll).order_by('?')
	else:
		questions = models.Question.objects.filter(poll=poll).order_by('order')

	choices = models.Choice.objects.filter(question__in=questions)

	if (not anonymous_poll):
		try:
			response = models.Response.objects.get(poll=poll, user=request.user)
		except ObjectDoesNotExist:
			response = None
	else:
		response = poll_invitation.response


	error_msg = None;
	if (request.method == 'POST') and not try_poll:

		if response is not None:
			response.choices.clear()
			models.Verbatim.objects.filter(response=response).delete()
		else:
			try:
				response = models.Response(poll=poll, user=request.user)
			except ValueError:
				if anonymous_poll:
					response = models.Response(poll=poll, user=None)
					poll_invitation.response = response
					poll_invitation.save()
				else:
					set_cache_message(request.user, 'error', "Unexpected error occurred when attempting to save your response. Please contact the administrator.")
					return HttpResponseRedirect(request.path)

			response.save()

		for field, value in request.POST.items():
			if re.match('^q\d*_choice\d*$', field) == None:
				continue
			try:
				choice = models.Choice.objects.get(pk=int(value), question__poll=poll)
				response.choices.add(choice)

				if not choice.is_fixed:
					v = models.Verbatim(response=response, choice=choice, verbatim=request.POST['%s_verbatim' % choice.pk])
					v.save()

			except (ObjectDoesNotExist, ValueError):
				error_msg = "Corrupted data, please try again."
				break

		if error_msg:
			set_cache_message(request.user, "error", error_msg)
			response.delete();

		else:
			if request.user.is_authenticated():
				error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)
			cs = response.choices.all()
			completed = True
			for q in models.Question.objects.filter(poll=poll):
				if not cs.exists():
					completed = False
					break
				cs = cs.exclude(question=q)

			if completed: # Complete also saves the Response
				set_cache_message(request.user, "success", "You have successfully completed the poll. Thank you!")
				response.set_complete()
			else:
				set_cache_message(request.user, "info", "The poll has not been completed. You may finish it in the \"Ongoing Polls\" section at the home page.")

			return HttpResponseRedirect('/polls/home/')

	elif request.user.is_authenticated():
			error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)

	if anonymous_poll:
		template = "non-auth-do_survey.html"
		username = None
	else:
		template = "do_survey.html"
		username = request.user.username

	return render(request, 'polls/%s' % template,
								{'poll':poll,
									'username':username,
									'questions':questions,
									'choices':choices,
									'response':response,
									'try_poll':try_poll,
									'error_msg':error_msg,
									'anonymous_poll':anonymous_poll,
									'is_pollster':is_pollster});

@login_required(login_url='/polls/login')
def review_survey(request, poll_id):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False

	try:
		poll = models.Poll.objects.get(pk=poll_id)
		response = models.Response.objects.get(poll=poll, user=request.user)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "You have not completed this poll yet.")
		return HttpResponseRedirect('/polls/home/')

	if (not response.is_completed):
		set_cache_message(request.user, 'error', "You have not completed this poll yet.")
		return HttpResponseRedirect('/polls/home/')


	questions = models.Question.objects.filter(poll=poll)
	choices = models.Choice.objects.filter(question__in=questions)

	error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)
	return render(request, 'polls/review_survey.html',
								{'response':response,
									'username':request.user.username,
									'choices':choices,
									'questions':questions,
									'poll':poll,
									'error_msg':error_msg,
									'is_pollster':is_pollster});

@login_required(login_url='/polls/login')
def remove_response(request, poll_id):
	try:
		response = models.Response.objects.get(poll__pk=poll_id, user=request.user)
		response.delete()
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "You have not completed this poll yet.")

	return HttpResponseRedirect('/polls/home/')

@login_required(login_url='/polls/login')
def home(request):
	home_active = 'active'

	# Checking pollster permission
	try:
		g = request.user.groups.get(name='sys_pollsters')
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False

	public_polls = models.Poll.objects.filter(poll_status=models.Poll.ST_PUBLISHED, access_type=models.Poll.AT_PUBLIC, is_finished=False).exclude(user=request.user)
	restricted_polls = models.Poll.objects.filter(poll_status=models.Poll.ST_PUBLISHED, access_type=models.Poll.AT_RESTRICTED, allowed_groups__in=request.user.groups.all(), is_finished=False).exclude(user=request.user)
	private_polls = models.Poll.objects.filter(poll_status=models.Poll.ST_PUBLISHED, access_type=models.Poll.AT_PRIVATE, allowed_users=request.user, is_finished=False).exclude(user=request.user)

	if (public_polls or restricted_polls or private_polls):

		available_polls = list(chain(public_polls, private_polls, restricted_polls))
	else:
		available_polls = None


	responses = models.Response.objects.filter(user=request.user)
	completed_polls = responses.exclude(is_completed=False)
	ongoing_polls = responses.exclude(is_completed=True, poll__is_finished=False)

	pprint("available_polls before: ", stream=sys.stderr)
	pprint(available_polls, stream=sys.stderr)

	if responses.exists() and available_polls is not None:
		for response in responses:
			if response.poll in available_polls:
				available_polls.remove(response.poll)

	pprint("available_polls after: ", stream=sys.stderr)
	pprint(available_polls, stream=sys.stderr)

	error_msg, warning_msg, success_msg, info_msg = caches_messages(request.user)
	return render(request, 'polls/home.html',
								{'available_polls':available_polls,
									'username':request.user.username,
									'completed_polls':completed_polls,
									'ongoing_polls':ongoing_polls,
									'error_msg':error_msg,
									'warning_msg':warning_msg,
									'success_msg':success_msg,
									'info_msg':info_msg,
									'home_active':home_active,
									'is_pollster':is_pollster});

@login_required(login_url='/polls/login')
def view_stats(request, poll_id):
	mypolls_active = "active"
	css_file = "view_stats.css"
	js_file = "view_stats.js"


	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "Sorry! The poll you are trying to see the statistics from, does not exists anymore.")
		return HttpResponseRedirect("/polls/manage-poll/%s/" % poll_id)

	questions = models.Question.objects.filter(poll=poll)
	choices = models.Choice.objects.filter(question__in=questions)
	verbatims = models.Verbatim.objects.filter(choice__in=choices)

	print("Preguntas: %d" % questions.count())
	print("Opciones: %d" % choices.count())
	print("Verbatims: %d" % verbatims.count())

	return render(request, 'polls/view_stats.html',
								{'poll':poll,
									'username':request.user.username,
									'questions':questions,
									'choices':choices,
									'verbatims':verbatims,
									'css_file':css_file,
									'mypolls_active':mypolls_active,
									'is_pollster':is_pollster,
									'js_file':js_file});

@login_required(login_url='/polls/login')
def account(request):
	account_active = 'active'
	password_error = None
	user_error = None
	user_form = forms.UserProfileForm(instance=request.user)
	password_form = forms.PasswordChangeForm()


	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False

	if (request.method == 'POST'):

		if (request.POST['submit'] == 'Save'):
			user_form = forms.UserProfileForm(request.POST, instance=request.user)
			if user_form.is_valid():
				user_form.save()

		else:
			password_form = forms.PasswordChangeForm(request.POST)
			if password_form.is_valid():
				old_password = password_form.cleaned_data['old_password']
				password = password_form.cleaned_data['password']
				cpassword = password_form.cleaned_data['confirm_password']

				if not (request.user.check_password(old_password)):
					password_error = 'Wrong password. Please try again.'

				elif (password != cpassword):
					password_error = "New passwords don't match. Please try again."

				else:
					request.user.set_password(password)
					request.user.save()

	return render(request, 'polls/account.html',
								{'user_form':user_form,
									'password_form': password_form,
									'account_active':account_active,
									'username':request.user.username,
									'password_error':password_error,
									'user_error':user_error,
									'is_pollster':is_pollster});

def about(request):
	about_active = 'active'
	is_pollster = False

	if request.user.is_authenticated():
		template = 'polls/about.html'
		username = request.user.username
		# Checking pollster permission
		try:
			g = request.user.groups.get(name="sys_pollsters")
			is_pollster = True

		except ObjectDoesNotExist:
			is_pollster = False

	else:
		username = ''
		template = 'polls/non-auth-about.html'

	return render(request, template, {'about_active':about_active, 'is_pollster':is_pollster, 'username':username});


def contact(request):
	contact_active = 'active'
	is_pollster = False

	if request.user.is_authenticated():
		template = 'polls/contact.html'
		username = request.user.username
		# Checking pollster permission
		try:
			g = request.user.groups.get(name="sys_pollsters")
			is_pollster = True

		except ObjectDoesNotExist:
			pass
	else:
		template = 'polls/non-auth-contact.html'
		username = ''

	return render(request, template, {'contact_active':contact_active, 'is_pollster':is_pollster, 'username':username});


@login_required(login_url='/polls/login')
def export_poll(request, poll_id):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
	except ObjectDoesNotExist:
		set_cache_message(request.user, 'error', "Sorry! The poll you are trying to export does not exist anymore.")
		return HttpResponseRedirect("/polls/my-polls/%s/" % poll_id)

	poll_json =  poll.get_json()
	json_response = JsonResponse(poll_json, safe=False)
	json_response['Content-Disposition'] = 'attachment; filename=%s.json' % poll.name
	return json_response

@login_required(login_url='/polls/login')
def get_csv_stats(request, poll_id, delimiter=','):

	# Checking pollster permission
	try:
		g = request.user.groups.get(name="sys_pollsters")
		is_pollster = True

	except ObjectDoesNotExist:
		is_pollster = False
		set_cache_message(request.user, "error", "Sorry, you don't have permission to access this area. Redirecting to home page...")
		return HttpResponseRedirect('/polls/home/')

	try:
		poll = models.Poll.objects.get(pk=poll_id, user=request.user)
		poll_csv = poll.get_responses_csv()

		csv_response = HttpResponse(content_type='text/csv')
		csv_response['Content-Disposition'] = 'attachment; filename=%s_stats.csv' % poll.name

		writer = csv.writer(csv_response, delimiter=delimiter)
		writer.writerows(poll_csv)

		return csv_response

	except ObjectDoesNotExist:
		 return page_not_found(request)
