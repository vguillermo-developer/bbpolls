from django.conf.urls import url
from polls import views

urlpatterns = [
    url(r'login/$', views.login_view, name='login'),
	url(r'activate-account/(?P<activation_key>[0-9a-f]+)/$', views.activate_account, name='activate-account'),
	url(r'logout/$', views.logout_view, name='logout'),
	url(r'home/$', views.home, name='home'),
	url(r'review-poll/(?P<poll_id>[0-9]+)/$', views.review_survey, name='review-poll'),
	url(r'review-poll/(?P<poll_id>[0-9]+)/remove/$', views.remove_response, name='remove-response'),
	url(r'my-polls/$', views.polls_index, name='my-polls'),
	url(r'export-poll/(?P<poll_id>[0-9]+)/$', views.export_poll, name='export-poll'),
	url(r'send-poll/(?P<poll_id>[0-9]+)/$', views.send_poll, name='send-poll'),
	url(r'create-poll/$', views.create_poll, name='create-poll'),
	url(r'unpublish-poll/(?P<poll_id>[0-9]+)/$', views.unpublish_poll, name='unpublish-poll'), #Needs to come first due to 'publish-poll' can also partially match with 'unpublish_poll' url
	url(r'publish-poll/(?P<poll_id>[0-9]+)/$', views.publish_poll, name='publish-poll'),
	url(r'archive-poll/(?P<poll_id>[0-9]+)/$', views.archive_poll, name='archive-poll'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/$', views.manage_poll, name='manage-poll'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/add-question/$', views.add_question, name='add-question'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/increase-question-order/(?P<question_id>[0-9]+)(?:/(?P<scroll>[0-9]+))?/$', views.increase_question_order, name='increase-question-order'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/decrease-question-order/(?P<question_id>[0-9]+)/(?:(?P<scroll>[0-9]+))?/$', views.decrease_question_order, name='decrease-question-order'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/manage-question/(?P<question_id>[0-9]+)/$', views.manage_question, name='manage-question'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/manage-question/(?P<question_id>[0-9]+)/remove/$', views.remove_question, name='remove-question'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/manage-question/(?P<question_id>[0-9]+)/add-multimedia-source-url/$', views.add_multimedia_source, {'source':'url'}, name='add-mm-src-url'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/manage-question/(?P<question_id>[0-9]+)/add-multimedia-source-file/$', views.add_multimedia_source, {'source':'file'}, name='add-mm-src-file'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/manage-question/(?P<question_id>[0-9]+)/remove-multimedia-source/(?P<mmsrc_id>[0-9]+)/$', views.remove_multimedia_source, name='remove-mm-src'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/clone/$', views.clone_poll, name='clone-poll'),
	url(r'manage-poll/(?P<poll_id>[0-9]+)/remove/$', views.remove_poll, name='remove-poll'),
	url(r'view-stats/(?P<poll_id>[0-9]+)/$', views.view_stats, name='view-stats'),
	url(r'view-stats/(?P<poll_id>[0-9]+)/get-csv-stats-pc/$', views.get_csv_stats, {'delimiter':','}, name='get-csv-stats-pc'),
	url(r'view-stats/(?P<poll_id>[0-9]+)/get-csv-stats/$', views.get_csv_stats, {'delimiter':';'}, name='get-csv-stats'),
	url(r'try-poll/(?P<poll_id>[0-9]+)/$', views.do_survey, {'try_poll':True}, name='try-poll'),
	url(r'do-poll/(?P<poll_id>[0-9]+)/$', views.do_survey, name='do-poll'),
	url(r'anonymous-poll/(?P<poll_id>[0-9]+)/(?P<invitation_key>[0-9a-f]+)/$', views.do_survey, name='anonymous-poll'),
	url(r'account/$', views.account, name='account'),
	url(r'about/$', views.about, name='about'),
	url(r'contact/$', views.contact, name='contact')
]
