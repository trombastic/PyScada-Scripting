# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pyscada

__version__ = '0.7.0rc5'
__author__ = 'Martin Schröder'

default_app_config = 'pyscada.scripting.apps.PyScadaScriptingConfig'

parent_process_list = [{'pk': 95,
                        'label': 'pyscada.scripting',
                        'process_class': 'pyscada.scripting.worker.MasterProcess',
                        'process_class_kwargs': '{"dt_set":30}',
                        'enabled': True}]