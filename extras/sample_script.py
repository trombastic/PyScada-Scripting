#!/usr/bin/python
# -*- coding: utf-8 -*-

from time import time
import logging

logger = logging.getLogger(__name__)


def script(self):
    """
    write your code here, don't change the name of this function

    :return:
    """
    # read in the last 60 seconds from db
    data = self.read_values_from_db(variable_names=['value_1'],
                                    time_from=time()-60,
                                    time_to=time(),
                                    mean_value_period=0,
                                    no_mean_value=True)
    # data {'timevalues':[1530021334.0, 1530021336.0, 1530021339.0], 'value_1'[100, 200, 300]}

    data = self.read_values_from_db(variable_names=['t_7Ki_M'], current_value_only=True)
    # data {'timevalues': 1530021339.0, 'value_1': 300}

    logger.debug('debug message from the script')
    status = self.write_value_to_device(variable_name='value_1',
                                        value=True,
                                        time_start=time(),
                                        user=None,
                                        blocking=False,
                                        timeout=60)

    # write values to the database
    # only one value
    self.write_values_to_db(data={'value_2': [100]})  # assumes now() for time

    # multiple values with specific timestamps (dangerous! these values maybe not appear in the HMI)
    self.write_values_to_db(data={'value_3': [100, 200, 300],
                                  'value_4': [123, 333, 333],
                                  'timevalues':[1530021334.0, 1530021336.0, 1530021339.0]})
