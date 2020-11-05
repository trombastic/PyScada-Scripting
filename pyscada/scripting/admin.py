# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyscada.admin import admin_site
from pyscada.scripting.models import Script
from django.contrib import admin
import logging

logger = logging.getLogger(__name__)


class ScriptAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'active', 'interval', 'script_file',)
    list_editable = ('label', 'active', 'interval', 'script_file', )
    list_display_links = ('id',)


admin_site.register(Script, ScriptAdmin)
