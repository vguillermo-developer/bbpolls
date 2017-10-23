from django import template
from django.template.defaultfilters import stringfilter
from polls.models import *
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist

########## CUSTOM TEMPLATE FILTERS ###########
register = template.Library()


@register.filter(name = 'from_question')
def get_elements_from_question(elements, question):
    return elements.filter(question=question)

@register.filter(name = 'get_choice_checked')
def get_choice_checked(choice, response):
	if chioce in response.choices:
		return mark_safe("checked")
	else:
		return ""

@register.filter(name = 'get_verbatim_from_response_choice')
def get_verbatim_from_response_choice(choice, response):
	try:
		verbatim = Verbatim.objects.get(choice=choice, response=response)
	except ObjectDoesNotExist:
		verbatim=''

	return verbatim

@register.filter(name = 'get_verbatims_from_choice')
def get_verbatims_from_choice(verbatims, choice):
	return verbatims.filter(choice=choice)

@register.filter(name = 'is_checked')
def is_checked_choice(choice, response):
	return choice in response.choices.all()

@register.filter(name = 'is_choice_fixed')
def is_choice_fixed(choice):
	return (choice.type == Choice.FIXED)

def allows_multiple_answer(question):
	return question.answer_type == Question.MULTIPLE

@register.filter(name = 'display_error')
def display_error(msg):
	if msg and not msg.isspace():
		return mark_safe("<div class='col-md-8 col-md-offset-2 alert alert-danger' role='alert'><p><span class='glyphicon glyphicon-warning-sign'></span>&nbsp;%s</p></div>" % msg)
	else:
		return ''

@register.filter(name = 'display_info')
def display_info(msg):
	if msg and not msg.isspace():
		return mark_safe("<div class='col-md-8 col-md-offset-2 alert alert-info' role='alert'><p><span class='glyphicon glyphicon-info-sign'></span>&nbsp;%s</p></div>" % msg)
	else:
		return ''

@register.filter(name = 'display_success')
def display_success(msg):
	if msg and not msg.isspace():
		return mark_safe("<div class='col-md-8 col-md-offset-2 alert alert-success' role='alert'><p><span class='glyphicon glyphicon-thumbs-up'></span>&nbsp;%s</p></div>" % msg)
	else:
		return ''

@register.filter(name = 'render_help_text')
def render_help_text(field):
	if hasattr(field, 'help_text'):
		retval = field.help_text
		field.help_text = None
		return retval
