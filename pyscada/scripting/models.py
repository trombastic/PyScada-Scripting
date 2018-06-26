# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from os import getpid
import traceback

import logging
logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Script(models.Model):
    id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=255,default='', blank=True)
    active = models.BooleanField(default=True)
    interval_choices = (
        (0.1, '100 Milliseconds'),
        (0.5, '500 Milliseconds'),
        (1.0, '1 Second'),
        (5.0, '5 Seconds'),
        (10.0, '10 Seconds'),
        (15.0, '15 Seconds'),
        (30.0, '30 Seconds'),
        (60.0, '1 Minute'),
        (150.0, '2.5 Mintues'),
        (300.0, '5 Minutes'),
        (360.0, '6 Minutes (10 times per Hour)'),
        (600.0, '10 Minutes'),
        (900.0, '15 Minutes'),
        (1800.0, '30 Minutes'),
        (3600.0, '1 Hour'),
    )
    interval = models.FloatField(default=5, choices=interval_choices)
    script_file = models.CharField(max_length=255, default='', help_text='')

    def __str__(self):
        return '%s: (%s | %s)'%(self.label,self.script_file, self.class_name)




