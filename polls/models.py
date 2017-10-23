from datetime import datetime, timedelta
from django.contrib.auth.models import User, Group
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import models, IntegrityError
from django.db.models import Q
from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch.dispatcher import receiver
from django.forms import ValidationError
from django.utils.dateformat import DateFormat
from polls.includes import email_messages

import requests, re, hashlib, json, time

#################### POLLS ####################
#################### POLLS->POLL ####################
class Poll(models.Model):

	EXPORT_VALIDATION_SALT = "bbpolls_platform_import_key_48480183"

	AT_PUBLIC = 'PUBLIC'
	AT_RESTRICTED = 'RESTRICTED'
	AT_PRIVATE = 'PRIVATE'
	ACCESS_TYPE = (
		(AT_PUBLIC, 'Public'),
		(AT_RESTRICTED, 'Restricted'),
		(AT_PRIVATE, 'Private'),
	)

	ST_PUBLISHED = 'PUBLISHED'
	ST_DRAFT = 'DRAFT'
	ST_ARCHIVED = 'ARCHIVED'
	POLL_STATUS = (
		(ST_PUBLISHED, 'Published'),
		(ST_DRAFT, 'Draft'),
		(ST_ARCHIVED, 'Archived')
	)

	YES_NO_FIELD = (
		(True, 'Yes'),
		(False, 'No')
	)

	# Attributes
	name 				= models.CharField(max_length=200)
	created 			= models.DateTimeField('Created', auto_now_add=True, blank=True)
	last_modified 		= models.DateTimeField('Last Modified', auto_now=True, blank=True)
	user 				= models.ForeignKey(User, related_name="owner")
	access_type 		= models.CharField(choices=ACCESS_TYPE, default=AT_PUBLIC, max_length=15)
	allowed_groups 		= models.ManyToManyField(Group, blank=True, related_name="poll_allowed_groups", limit_choices_to=~Q(name__startswith="sys_"))
	allowed_users		= models.ManyToManyField(User, blank=True, related_name="poll_allowed_users")
	votes 				= models.IntegerField(default=0)
	poll_status 		= models.CharField(choices=POLL_STATUS, default=ST_DRAFT, max_length=50)
	archive_date		= models.DateTimeField('Archive Date', auto_now_add=False, blank=True, null=True)
	publish_date		= models.DateTimeField('Publish Date', auto_now_add=False, blank=True, null=True)
	randomize_questions = models.BooleanField(choices=YES_NO_FIELD, default=False)
	is_anonymous 		= models.BooleanField(choices=YES_NO_FIELD, default=False)
	is_finished 		= models.BooleanField(choices=YES_NO_FIELD, default=False)


	@property
	def times_answered(self):
		return Response.objects.filter(poll=self, is_completed=True).count()

	@property
	def number_questions(self):
		return Question.objects.filter(poll=self).count()

	@property
	def is_draft(self):
		return self.poll_status == Poll.ST_DRAFT

	@property
	def is_published(self):
		return self.poll_status == Poll.ST_PUBLISHED

	@property
	def is_archived(self):
		return self.poll_status == Poll.ST_ARCHIVED

	@property
	def is_doable(self):
		for q in Question.objects.filter(poll=self):
			if not q.is_doable:
				return False

		return True

	def __str__(self):
		return self.name


	def clone(self):

		questions = Question.objects.filter(poll=self).order_by('order')
		new_poll = self
		new_poll.name = '[COPY %d] %s' % (time.time()*10, self.name)
		new_poll.pk = None
		new_poll.poll_status = Poll.ST_DRAFT
		new_poll.votes = 0
		new_poll.save()

		for q in questions:
			q.clone(new_poll)


		new_poll.save()

		return new_poll


	def increase_votes(self):
		self.votes += 1
		self.save()


	def decrease_votes(self):
		self.votes -= 1
		self.save()


	def get_json(self):
		poll_data = serializers.serialize("json",
										Poll.objects.filter(pk=self.pk),
										fields=("name",
											"number_questions",
											"access_type",
											"randomize_questions",
											"is_anonymous"))

		questions_data = {}

		# Questions
		for question in Question.objects.filter(poll=self).order_by('order'):
			questions_data["question_%d" % question.order] = question.get_json()

		poll_json = {
			"poll" : poll_data,
			"allowed_groups" : None,
			"questions" : questions_data,
			"key" : Poll.get_import_validation_key(poll_data, questions_data)
		}

		return poll_json


	@staticmethod
	def get_import_validation_key(poll_data, questions_data):
		return hashlib.sha256((json.dumps(poll_data)+json.dumps(questions_data)+Poll.EXPORT_VALIDATION_SALT).encode('utf-8')).hexdigest()


	def send_poll(self, emails):
		return_codes = []
		registered_emails = []
		for e in emails:
			try:
				u = User.objects.get(email=e)
				self.allowed_users.add(u)
				registered_emails.append(e)

				msg = re.sub(email_messages.REG_INVITE_POLL_MESSAGE_PATTERNS['poll_name'], self.name, email_messages.REG_INVITE_POLL_MESSAGE)
				msg = re.sub(email_messages.REG_INVITE_POLL_MESSAGE_PATTERNS['poll_id'], "%d" % self.pk, msg)
				subject = re.sub(email_messages.REG_INVITE_POLL_SUBJECT_PATTTERNS['poll_name'], self.name, email_messages.REG_INVITE_POLL_SUBJECT)

			except ObjectDoesNotExist:
				try:
					poll_invitation = AnonymousInvitation.objects.get(poll=self, email=e)
					if (poll_invitation.response is not None and poll_invitation.response.is_completed):
						continue

				except ObjectDoesNotExist:
					poll_invitation = AnonymousInvitation(poll=self, email=e)
					poll_invitation.save()


				msg = re.sub(email_messages.ANON_INVITE_POLL_MESSAGE_PATTERNS['poll_name'], self.name, email_messages.ANON_INVITE_POLL_MESSAGE)
				msg = re.sub(email_messages.ANON_INVITE_POLL_MESSAGE_PATTERNS['poll_id'], "%d" % self.pk, msg)
				msg = re.sub(email_messages.ANON_INVITE_POLL_MESSAGE_PATTERNS['invite_key'], poll_invitation.key, msg)
				subject = re.sub(email_messages.ANON_INVITE_POLL_SUBJECT_PATTTERNS['poll_name'], self.name, email_messages.ANON_INVITE_POLL_SUBJECT)

			return_codes.append(send_mail(subject, msg, None, [e], fail_silently=False))

		return return_codes;




	@staticmethod
	def import_poll(poll_json, user):

		if (poll_json['key'] != Poll.get_import_validation_key(poll_json['poll'], poll_json['questions'])):
			raise ValidationError("The file is corrupted, can't import data.")

		for imported_poll in serializers.deserialize("json", poll_json['poll']):
			poll = Poll(user = user,
						name = imported_poll.object.name,
						access_type = imported_poll.object.access_type,
						randomize_questions = imported_poll.object.randomize_questions,
						is_anonymous = imported_poll.object.is_anonymous)

			poll.save()

			questions_json = poll_json['questions']
			for key in questions_json:
				for imported_question in serializers.deserialize("json", questions_json[key]['question']):

					question = Question(poll = poll,
									answer_type = imported_question.object.answer_type,
									question = imported_question.object.question,
									media_content = imported_question.object.media_content)
					question.save()

					for imported_choice in serializers.deserialize("json", questions_json[key]['choices']):

						choice = Choice(question = question,
							type = imported_choice.object.type,
							choice = imported_choice.object.choice
							)
						choice.save()

					for imported_mmsrc in serializers.deserialize("json", questions_json[key]['multimedia_sources']):

						mmsrc = MultimediaSource(question = question,
							media_type = imported_mmsrc.object.media_type,
							source_type = imported_mmsrc.object.source_type,
							url_source = imported_mmsrc.object.url_source,
							# file_source = imported_mmsrc.object.file_source,
							mime_type = imported_mmsrc.object.mime_type)
						try:
							mmsrc.validate_mime_type()
							mmsrc.save()
						except ValidationError:
							pass
		return poll

	def get_responses_csv(self):

		questions = Question.objects.filter(poll=self, answer_type=Question.UNIQUE).order_by('order')
		responses = Response.objects.filter(poll=self, is_completed=True)
		csv = [];
		row = []

		#  CSV header
		for q in questions:
			row.append("Question %d" % q.order)

		csv.append(row)

		#  CSV data
		for r in responses:
			row = []
			for c in r.choices.filter(question__answer_type=Question.UNIQUE).order_by('question__order'):
				row.append("Choice %d" % c.order)

			csv.append(row)

		return csv


#################### POLLS->QUESTION ####################
class Question(models.Model):

	# Constants
	UNIQUE = 'UNIQUE'
	MULTIPLE = 'MULTIPLE'
	ANSWER_TYPE = (
		(UNIQUE, 'Unique'),
		(MULTIPLE, 'Multiple'),
	)

	NONE_CONTENT = "NONE"
	IMAGE_CONTENT = "IMAGE"
	AUDIO_CONTENT = "AUDIO"
	VIDEO_CONTENT = "VIDEO"
	IFRAME_CONTENT = "IFRAME"

	MEDIA_CONTENT = (
		(NONE_CONTENT, "None"),
		(IMAGE_CONTENT, "Image"),
		(AUDIO_CONTENT, "Audio"),
		(VIDEO_CONTENT, "Video"),
		(IFRAME_CONTENT, "Iframe"),
	)

	# Atributes
	poll 			= models.ForeignKey(Poll)
	answer_type 	= models.CharField(choices=ANSWER_TYPE, default=UNIQUE, max_length=10)
	question 		= models.CharField(max_length=1000)
	created 		= models.DateTimeField('Created', auto_now_add=True)
	last_modified 	= models.DateTimeField('Last Modified', auto_now=True)
	media_content 	= models.CharField(choices=MEDIA_CONTENT, default=NONE_CONTENT, max_length=20)
	order 			= models.IntegerField(default=0);

	@property
	def number_choices(self):
		return Choice.objects.filter(question=self).count()

	# Methods
	def __str__(self):
		return self.question

	@property
	def is_doable(self):
		if (self.number_choices > 0):
			fixed_choices = 0
			free_choices = 0

			for c in Choice.objects.filter(question=self):
				fixed_choices += c.type == Choice.FIXED
				free_choices += c.type == Choice.FREE

				if (fixed_choices >= 2) or (fixed_choices >= 1):
					return True
		else:
			return False


	def clone(self, poll):
		choices = Choice.objects.filter(question=self)

		new_question = self
		new_question.poll = poll
		new_question.pk = None
		new_question.save()

		for c in choices:
			c.clone(new_question)

	def get_json(self):
		question_fields = ("answer_type", "question", "order")
		question_data = serializers.serialize("json", Question.objects.filter(pk=self.pk), fields = question_fields)

		multimedia_fields = ("media_type", "source_type", "url_source")#, "file_source")
		multimedia_data = serializers.serialize("json", MultimediaSource.objects.filter(question=self), fields = multimedia_fields)

		choices_fields = ("type", "choice")
		choices_data = serializers.serialize("json", Choice.objects.filter(question=self), fields = choices_fields)

		question_json = {
			"question" : question_data,
			"multimedia_sources" : multimedia_data,
			"choices" : choices_data
		}

		return question_json;


	def increase_order(self):
		if self.order < self.poll.number_questions-1:
			next_q = Question.objects.all().get(poll=self.poll, order=self.order+1);
			next_q.order -= 1;
			next_q.save();
			self.order += 1;
			self.save();


	def decrease_order(self):
		if self.order > 0:
			prev_q = Question.objects.all().get(poll=self.poll, order=self.order-1);
			prev_q.order += 1;
			prev_q.save();
			self.order -= 1;
			self.save();

	# Properties
	@property
	def allows_multiple_answer(self):
		return self.answer_type == Question.MULTIPLE

	@property
	def has_audio(self):
		audio_type = (self.media_content == Question.AUDIO_CONTENT)
		audio_srcs = MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.AUDIO_MEDIA_TYPE).exists()

		return (audio_type and audio_srcs)

	@property
	def number_audio_srcs(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.AUDIO_MEDIA_TYPE).count();

	@property
	def audio_sources(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.AUDIO_MEDIA_TYPE)

	@property
	def has_image(self):
		image_type = (self.media_content == Question.IMAGE_CONTENT)
		image_srcs = MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.IMAGE_MEDIA_TYPE).exists()

		return (image_type and image_srcs)

	@property
	def number_image_srcs(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.IMAGE_MEDIA_TYPE).count();

	@property
	def image_sources(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.IMAGE_MEDIA_TYPE)

	@property
	def has_iframe(self):
		iframe_type = (self.media_content == Question.IFRAME_CONTENT)
		iframe_srcs = MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.IFRAME_MEDIA_TYPE).exists()

		return (iframe_type and iframe_srcs)

	@property
	def number_iframe_srcs(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.IMAGE_MEDIA_TYPE).count();

	@property
	def iframe_sources(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.IFRAME_MEDIA_TYPE)

	@property
	def has_video(self):
		video_type = (self.media_content == Question.VIDEO_CONTENT)
		video_srcs = MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.VIDEO_MEDIA_TYPE).exists()

		return (video_type and video_srcs)

	@property
	def number_video_srcs(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.VIDEO_MEDIA_TYPE).count();

	@property
	def video_sources(self):
		return MultimediaSource.objects.filter(question=self, media_type=MultimediaSource.VIDEO_MEDIA_TYPE)

#################### POLLS->CHOICE ####################
class Choice(models.Model):
	# Constants
	FIXED = 'FIXED'
	FREE = 'FREE'
	CHOICE_TYPE = (
		(FIXED, 'Fixed'),
		(FREE, 'Free'),
	)

	# Atributes
	question = models.ForeignKey(Question)
	type = models.CharField(choices=CHOICE_TYPE, default=FIXED, max_length=10)
	choice = models.CharField(max_length=1000)
	created = models.DateTimeField('Created', auto_now_add=True)
	last_modified = models.DateTimeField('Last Modified', auto_now=True)
	votes = models.IntegerField(default=0)
	order = models.IntegerField(default=0)

	# Methods
	def __str__(self):
		return self.choice

	def clone(self, question):
		new_choice = self
		new_choice.question = question
		new_choice.pk = None
		new_choice.votes=0
		new_choice.save()

	def increase_votes(self):
		self.votes += 1
		self.save()

	def decrease_votes(self):
		if self.votes > 0:
			self.votes -= 1
			self.save()

	# Properties
	@property
	def is_fixed(self):
		return self.type == Choice.FIXED;

	@property
	def response_percentage(self):
		if (self.question.poll.votes > 0):
			percent = (float(self.votes)/float(self.question.poll.votes))*100
			print(percent)
		else:
			percent = 0

		return "%d" % percent

#################### /POLLS ####################

#################### RESPONSES ####################
class Response(models.Model):

	class Meta:
		unique_together = ['user', 'poll']

	poll = models.ForeignKey(Poll, on_delete=models.PROTECT)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
	choices = models.ManyToManyField(Choice)
	created = models.DateTimeField('Created', auto_now_add=True)
	is_completed = models.BooleanField(default=False);

	def set_complete(self):
		self.is_completed = True
		self.poll.increase_votes()

		for c in self.choices.all():
			c.increase_votes()

		created = datetime.now();
		self.save()

class Verbatim(models.Model):
	choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
	response = models.ForeignKey(Response, on_delete=models.CASCADE)
	verbatim = models.CharField(max_length=1000, blank=True)

	def __str__(self):
		return self.verbatim

	@property
	def title(self):
		if (self.response.poll.is_anonymous):
			title = "%s" % (self.response.created.strftime('%d-%m-%Y %H:%M:%S'))
		else:
			title = "%s - %s" % (self.response.user.email, self.response.created.strftime('%d-%m-%Y %H:%M:%S'))

		return title

#################### /RESPONSES ####################

#################### POLLS->ANONYMOUS POLL INVITATION ####################

class AnonymousInvitation(models.Model):

	INVITE_VALIDATION_SALT = "bbpolls_platform_invite_key_87654258"

	class Meta:
		unique_together = ['poll', 'email']

	# Atributes
	poll 		= models.ForeignKey(Poll)
	response 	= models.ForeignKey(Response, blank=True, null=True)
	email 		= models.CharField(max_length=200)
	key         = models.CharField(max_length=500, blank=True, null=True)

##########################################################################


#################### MULTIMEDIA ####################
class MultimediaSource(models.Model):

	# Constants
	IMAGE_MEDIA_TYPE = "IMAGE"
	AUDIO_MEDIA_TYPE = "AUDIO"
	VIDEO_MEDIA_TYPE = "VIDEO"
	IFRAME_MEDIA_TYPE = "IFRAME"

	MEDIA_TYPE_LIST = (
		(IMAGE_MEDIA_TYPE, "Image"),
		(AUDIO_MEDIA_TYPE, "Audio"),
		(VIDEO_MEDIA_TYPE, "Video"),
		(IFRAME_MEDIA_TYPE, "Iframe"),
	)

	URL_SRC = "URL"
	FILE_SRC = "FILE"

	SOURCE_TYPE_LIST = (
		(URL_SRC, "Url"),
		(FILE_SRC, "File"),
	)

	## Browsers supported MIME TYPES
	CHROME_AUDIO_EXTENSIONS =['audio/mpeg', 'audio/ogg', 'audio/wav']
	CHROME_VIDEO_EXTENSIONS = ['video/mp4', 'video/ogg', 'video/webm']

	FIREFOX_AUDIO_EXTENSIONS = ['audio/mpeg', 'audio/ogg', 'audio/wav']
	FIREFOX_VIDEO_EXTENSIONS = ['video/mp4', 'video/ogg', 'video/webm']

	IE_AUDIO_EXTENSIONS = ['audio/mpeg']
	IE_VIDEO_EXTENSIONS = ['video/mp4']

	OPERA_AUDIO_EXTENSIONS = ['audio/ogg', 'audio/wav']
	OPERA_VIDEO_EXTENSIONS = ['video/ogg', 'video/webm']

	SAFARI_AUDIO_EXTENSIONS = ['audio/mpeg', 'audio/wav']
	SAFARI_VIDEO_EXTENSIONS = ['video/mp4']

	## Supported MIME TYPES
	IMAGE_SUPPORTED_EXTENSIONS = ['image/jpeg', 'image/png', 'image/gif']
	AUDIO_SUPPORTED_EXTENSIONS = ['audio/mpeg', 'audio/ogg', 'audio/wav']
	VIDEO_SUPPORTED_EXTENSIONS = ['video/mp4', 'video/ogg', 'video/webm']
	IFRAME_SUPPORTED_EXTENSIONS = ['application/javascript', 'text/javascript', 'text/html']

	# Atributes
	question = models.ForeignKey(Question)
	media_type = models.CharField(choices=MEDIA_TYPE_LIST, default=IMAGE_MEDIA_TYPE, max_length=20)
	source_type = models.CharField(choices=SOURCE_TYPE_LIST, default=URL_SRC, max_length=20)
	# file_source = models.FileField(upload_to="%d_tmp" % question.othermodel.pk, blank=True, null=True)
	url_source = models.URLField(max_length=2000, blank=True, null=True)

	# Fills on validation
	mime_type = models.CharField(max_length=50, blank=True)

	# Methods
	def validate_mime_type(self):
		if self.source_type == MultimediaSource.URL_SRC:
			r = requests.get(self.url_source)
			if r.status_code != 200:
				raise ValidationError("Can't reach url")

			self.mime_type = r.headers['content-type']
			r.close()

			if self.media_type == MultimediaSource.AUDIO_MEDIA_TYPE:
				if not self.mime_type in MultimediaSource.AUDIO_SUPPORTED_EXTENSIONS:
					raise ValidationError('Unsupported mime type of audio source. Supported audio mime types are: audio/mpeg, audio/ogg, audio/wav.')

			elif self.media_type == MultimediaSource.IMAGE_MEDIA_TYPE:
				if not self.mime_type in MultimediaSource.IMAGE_SUPPORTED_EXTENSIONS:
					raise ValidationError('Unsupported mime type of image source. Supported image mime types are: image/jpeg, image/png, image/gif.')

			elif self.media_type == MultimediaSource.VIDEO_MEDIA_TYPE:
				if not self.mime_type in MultimediaSource.VIDEO_SUPPORTED_EXTENSIONS:
					raise ValidationError('Unsupported mime type of video source. Supported video mime types are: video/mp4, video/ogg, video/webm.')

			elif self.media_type == MultimediaSource.IFRAME_MEDIA_TYPE:
				if not self.mime_type in MultimediaSource.IFRAME_SUPPORTED_EXTENSIONS:
					raise ValidationError('Unsupported mime type of iframe source. Supported iframe mime types are: application/javascript, text/javascript, text/html.')

			else:
				raise ValidationError('Unsupported mime type.')

		elif self.source_type == MultimediaSource.FILE_SRC:
			pass

		else:
			raise ValidationError('Unknown source type.')

	# Properties
	@property
	def name(self):
		# if source_type == 'url':
		# elif source_type == 'file':
			# return file_source.filename
		# if (self.mime_type in MultimediaSource.IFRAME_SUPPORTED_EXTENSIONS):
		# 	return self.url_source
		# else:
		return self.url_source.split('/')[-1]

	@property
	def get_source(self):
		if (self.source_type == MultimediaSource.URL_SRC):
			return self.url_source
		elif (self.source_type == MultimediaSource.FILE_SRC):
			pass

	@property
	def is_url(self):
		return self.source_type == MultimediaSource.URL_SRC

	@property
	def ie_supported(self):
		if self.media_type == MultimediaSource.AUDIO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.IE_AUDIO_EXTENSIONS
		elif self.media_type == MultimediaSource.VIDEO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.IE_VIDEO_EXTENSIONS
		else:
			return True

	@property
	def firefox_supported(self):
		if self.media_type == MultimediaSource.AUDIO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.FIREFOX_AUDIO_EXTENSIONS
		elif self.media_type == MultimediaSource.VIDEO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.FIREFOX_VIDEO_EXTENSIONS
		else:
			return True

	@property
	def chrome_supported(self):
		if self.media_type == MultimediaSource.AUDIO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.CHROME_AUDIO_EXTENSIONS
		elif self.media_type == MultimediaSource.VIDEO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.CHROME_VIDEO_EXTENSIONS
		else:
			return True
	@property
	def safari_supported(self):
		if self.media_type == MultimediaSource.AUDIO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.SAFARI_AUDIO_EXTENSIONS
		elif self.media_type == MultimediaSource.VIDEO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.SAFARI_VIDEO_EXTENSIONS
		else:
			return True
	@property
	def opera_supported(self):
		if self.media_type == MultimediaSource.AUDIO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.OPERA_AUDIO_EXTENSIONS
		elif self.media_type == MultimediaSource.VIDEO_MEDIA_TYPE:
			return self.mime_type in MultimediaSource.OPERA_VIDEO_EXTENSIONS
		else:
			return True
#################### /MULTIMEDIA ####################

#################### USER PROFILE ####################
class UserProfile(models.Model):
	user = models.OneToOneField(User)
	activation_key = models.CharField(max_length=40, blank=True)
	key_expires = models.DateTimeField(default=datetime.now())

	def activate_account(self, activation_key):
		if (self.activation_key == activation_key):
			# if (self.key_expires >= datetime.now()):
			self.user.is_active = True
			self.user.save()
			self.activation_key = ''
			self.save()
			return True
		else:
			return False

	def send_activation_email(self):
		msg = re.sub(email_messages.ACTIVATION_MESSAGE_PATTERNS['activation_key'], self.activation_key, email_messages.ACTIVATION_MESSAGE)
		code = send_mail(email_messages.ACTIVATION_SUBJECT, msg, None,[self.user.email], fail_silently=False)

		return code


	def __str__(self):
		return self.user.username

	class Meta:
		verbose_name_plural=u'User profiles'

#################### /USER PROFILE ####################



#################### Signals ####################
@receiver(pre_save, sender=Question)
def __on_question_creation(sender, instance, **kwargs):
	if (instance.pk == None and instance.poll is not None):
		instance.order = instance.poll.number_questions
		instance.poll.save()

@receiver(pre_delete, sender=Question)
def __on_question_deletion(sender, instance, **kwargs):
	for q in Question.objects.filter(poll=instance.poll):
		if (q.order > instance.order):
			q.order -= 1
			q.save();

	instance.poll.save()

@receiver(pre_save, sender=Choice)
def __on_choice_creation(sender, instance, **kwargs):
	if (instance.pk == None and instance.question is not None):
		instance.order = Choice.objects.filter(question=instance.question).count()+1


@receiver(pre_delete, sender=Choice)
def __on_choice_deletion(sender, instance, **kwargs):
	for c in Choice.objects.filter(question=instance.question, order__gt=instance.order):
			c.order -= 1
			c.save();

@receiver(post_save, sender=Question)
def __on_question_update(sender, instance, **kwargs):
	instance.poll.last_modified = datetime.now()
	instance.poll.save()

@receiver(pre_delete, sender=Response)
def __on_response_deletion(sender, instance, **kwargs):
	instance.poll.decrease_votes()
	for c in instance.choices.all():
		c.decrease_votes()

@receiver(post_save, sender=AnonymousInvitation)
def __on_anonymous_invitation_created(sender, instance, **kwargs):
	if (not instance.key):
		poll_json = serializers.serialize("json", Poll.objects.filter(pk=instance.poll.pk))
		instance.key = hashlib.sha256((json.dumps(poll_json)+instance.email+AnonymousInvitation.INVITE_VALIDATION_SALT).encode('utf-8')).hexdigest()
		instance.save()
