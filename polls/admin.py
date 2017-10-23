# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from polls.models import *

# Register your models here.
admin.site.register(Poll)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Response)
admin.site.register(Verbatim)
admin.site.register(AnonymousInvitation)
admin.site.register(UserProfile)
admin.site.register(MultimediaSource)
