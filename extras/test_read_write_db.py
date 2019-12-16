#!/usr/bin/python
# -*- coding: utf-8 -*-

from time import time
import logging

logger = logging.getLogger(__name__)


def startup(self):
    """
    write your code startup code here, don't change the name of this function
    :return:
    """
    self.counter = 0


def shutdown(self):
    """
    write your code shutdown code here, don't change the name of this function
    :return:
    """
    pass


def script(self):
    """
    write your code loop code here, don't change the name of this function

    :return:
    """
    self.counter += 1
    data = self.read_values_from_db(variable_names=['counter'], current_value_only=True, time_from=time()-5, time_to=time())
    if 'counter' in data:
        logger.debug('a %d: %d'%(self.counter, data['counter'][-1]))
    self.write_values_to_db(data={'counter': [self.counter]})  # assumes now() for time
    #data = self.read_values_from_db(variable_names=['counter'], current_value_only=True,time_from=time()-60, time_to=time())
    #if 'counter' in data:
    #    logger.debug('b %d: %d'%(self.counter, data['counter']))
