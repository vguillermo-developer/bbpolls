SIGNATURE = "Thank you very much!\n\
BBPolls Staff"

####################################
######### ACTIVATION EMAIL #########
####################################

ACTIVATION_MESSAGE_PATTERNS = {'activation_key':'{{ACTIVATION_KEY}}'}
ACTIVATION_SUBJECT = "BBPolls user activation email"
ACTIVATION_MESSAGE = \
"Thank you for registering into BBPolls.\n\
To activate your account simply click on the next url:\n\
http://localhost:8000/polls/activate-account/{{ACTIVATION_KEY}}/\n\
\n\
If you encounter any problems tu activate your account, please go to the next url, and send us a message.\n\
Your issue will be attended as soon as possible:\n\
http://localhost:8000/polls/contact/\n\
\n\
This is an auto-generated message for account activation. Please do not reply to this email.\n\
\n\
%s" % SIGNATURE

####################################
######### INVITATION EMAIL #########
####################################

# For registered member
REG_INVITE_POLL_MESSAGE_PATTERNS = {'poll_name':'{{POLL_NAME}}', 'poll_id':'{{POLL_ID}}'}
REG_INVITE_POLL_SUBJECT_PATTTERNS = {'poll_name':'{{POLL_NAME}}'}
REG_INVITE_POLL_SUBJECT = "BBPolls - Poll Invitation - {{POLL_NAME}}"
REG_INVITE_POLL_MESSAGE = "You have been invited to the poll: <b>{{POLL_NAME}}</b>\n\
\n\
You can completed it through this link:\n\
http://localhost:8000/polls/do-poll/{{POLL_ID}}/\n\
\n\
This is an auto-generated message. Please do not reply to this email.\n\
\n\
%s" % SIGNATURE


# For anonymous member
ANON_INVITE_POLL_MESSAGE_PATTERNS = {'invite_key':'{{INVITE_KEY}}', 'poll_name':'{{POLL_NAME}}', 'poll_id':'{{POLL_ID}}'}
ANON_INVITE_POLL_SUBJECT_PATTTERNS = {'poll_name':'{{POLL_NAME}}'}
ANON_INVITE_POLL_SUBJECT = "BBPolls - Poll Invitation - {{POLL_NAME}}"
ANON_INVITE_POLL_MESSAGE = "This is an invitation to complete a poll from the platform <a href='http://localhost:8000/polls/'>BBPolls</a>\n\
You have been invited to the poll: <b>{{POLL_NAME}}</b> \n\
\n\
You can completed it through this link:\n\
http://localhost:8000/polls/anonymous-poll/{{POLL_ID}}/{{INVITE_KEY}}/\n\
\n\
This is an auto-generated message. Please do not reply to this email.\n\
\n\
%s" % SIGNATURE
