#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyscada.scripting.worker import ScriptingProcess
from time import time
import logging

logger = logging.getLogger(__name__)


def script(self):
    """
    write your code here
    :return:
    """
    # just print a debug message to the log
    logger.debug('Scripting loop')


