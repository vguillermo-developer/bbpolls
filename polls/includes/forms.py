from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from polls import models
from multi_email_field.forms import MultiEmailField

class LoginForm(forms.Form):

	email = forms.CharField(
		max_length=100,
		widget=forms.TextInput(attrs={
			'placeholder': 'Email',
		}),
	)
	password = forms.CharField(
		max_length=100,
		widget=forms.PasswordInput(attrs={
			'placeholder': 'Password',
		}),

	)

class RegisterForm(forms.ModelForm):

	confirm_password = forms.CharField(
		max_length = 100,
		required = True,
		widget=forms.PasswordInput())

	class Meta:
		model = User
		fields = ['email', 'password', 'confirm_password', 'first_name', 'last_name']
		widgets ={
			'password' : forms.PasswordInput(),
		}

	def clean_email(self):
		email = self.cleaned_data.get('email')
		if email and User.objects.filter(email__iexact=email):
			raise forms.ValidationError(u'Email address must be unique.')
		return email

	def clean(self):
		cleaned_data = super(RegisterForm, self).clean()
		password = self.cleaned_data.get("password")
		cpassword = self.cleaned_data.get("confirm_password")

		if password != cpassword:
			raise forms.ValidationError("Passwords don't match")
			del cleaned_data["confirm_password"]
			del cleaned_data["password"]

		return cleaned_data

class PollForm(forms.ModelForm):

	class Meta:
		model = models.Poll
		fields = ['name', 'access_type', 'allowed_groups', 'is_anonymous', 'randomize_questions']
		help_texts = {
			'access_type': _('Public - Everyone can access the poll<br/>\
							  Restricted - Only users belonging to selected groups or invited directly can access the poll<br/>\
							  Private - Only users invited directly can access the poll'),
			'allowed_groups': _('Select the groups that are allowed to access the poll.<br/>\
								<i>*Note: This field is only meaningful if the Restricted acces type is set.<br/></i>'),
			'is_anonymous': _('If the poll is anonymous, the respondents\' contact and personal information will not be available for the pollster.'),
			'randomize_questions': _('If this option is active the questions will show to the user in random order. However,\
									 in the manage panel, the questions will appear always in the same order.'),
		}

	def disable(self):
		for f in self.fields:
			self.fields[f].widget.attrs['readonly'] = True
			self.fields[f].widget.attrs['disabled'] = True
			self.fields[f].widget.attrs['class'] = "disabled"



class PollCreateForm(forms.ModelForm):
	class Meta:
		model = models.Poll
		fields = ['name']
		# help_texts = {
		#           'access_type': _('Public - Everyone can access the poll<br/>\
		#           				  Restricted - Only users belonging to selected groups or invited directly can access the poll<br/>\
		#           				  Private - Only users invited directly can access the poll'),
		#           'randomize_questions': _('If this option is active the questions will show to the user in random order. However,\
		#           						 in the manage panel, the questions will appear always in the same order.'),
		#       }

class SendPollForm(forms.Form):
	emails = forms.CharField(
		widget = forms.Textarea(attrs={
			'placeholder': 'Type the emails, separated by semicolon (;)',
			'cols' : '100',
			'rows' : '100'
		}),
		label = 'Emails',
		help_text = 'Type all the emails which you want to receive the poll invitation'
	)

class QuestionForm(forms.ModelForm):

	class Meta:
		model = models.Question
		fields = ['question', 'answer_type', 'media_content']

		labels = {
			'media_content': _('Media Content Type'),
		}

		help_texts = {
			'answer_type': _('Unique - Only one choice can be selected<br/>\
							  Multiple - Can select more than one choice'),
			'media_content': _('Select the media content type that the question must show. To do this, first you have to \
								add a multimedia source in the table below.<br/>\
								Notice that you may have any number of multimedia sources of any kind, however the question will show only\
								the sources that matches with the "media content type" selected on this field.'),
		}

	def disable(self):
		for f in self.fields:
			self.fields[f].widget.attrs['readonly'] = True
			self.fields[f].widget.attrs['disabled'] = True
			self.fields[f].widget.attrs['class'] = "disabled"

class AddQuestionForm(forms.ModelForm):

	class Meta:
		model = models.Question
		fields = ['question', 'answer_type']

		help_texts = {
			'answer_type': _('Unique - Only one choice can be selected<br/>\
							  Multiple - Can select more than one choice'),
		}

class MultimediaSourceFormURL(forms.ModelForm):

	def add_error(self, field, msg):
		self._errors[field] = self.error_class([msg])

	class Meta:
		model = models.MultimediaSource
		fields = ['media_type', 'url_source']


class ChoiceForm(forms.ModelForm):

	class Meta:
		model = models.Choice
		fields = ['choice', 'type']

		help_texts = {
			'type': _("Fixed - The choice text is set by you.<br/>\
					  Free - The choice becomes an input, so the user himself writes the choice text.\
					   If this option is selected, the value that you set in the choice input will \
					   display as a title or legend for the choice input."),
		}

	def disable(self):
		for f in self.fields:
			self.fields[f].widget.attrs['readonly'] = True
			self.fields[f].widget.attrs['disabled'] = True
			self.fields[f].widget.attrs['class'] = "disabled"


class UserProfileForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		super(UserProfileForm, self).__init__(*args, **kwargs)
		self.fields['email'].widget.attrs['readonly'] = True
		self.fields['email'].widget.attrs['disabled'] = True
		self.fields['email'].widget.attrs['class'] = "disabled"


	class Meta:
		model = User
		fields = ['email', 'first_name', 'last_name']

	def clean_email(self):
		return self.instance.email

class PasswordChangeForm(forms.Form):

	old_password = forms.CharField(
		max_length = 100,
		required = True,
		widget=forms.PasswordInput(),
		label = "Old password"
	)

	password = forms.CharField(
		max_length = 100,
		required = True,
		widget=forms.PasswordInput(),
		label = 'New password'
	)

	confirm_password = forms.CharField(
		max_length = 100,
		required = True,
		widget=forms.PasswordInput(),
		label = 'Repeat new password'
	)

class PollImportForm(forms.Form):
	import_file = forms.FileField(
		allow_empty_file = False,
		#validators=[polls.includes.validators.MimetypeValidator(['application/json', 'text/plain'])],
		help_text="Upload a JSON file",
		label="Select file from your computer"
	)
