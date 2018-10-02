#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyscada.models import BackgroundProcess, Variable, RecordedData, DeviceWriteTask, VariableProperty
from pyscada.scripting.models import Script
import numpy as np
from pyscada.utils.scheduler import Process as BaseProcess

from os import getpid
import traceback

from time import time
import errno
from os import kill
import traceback
import json
import logging

logger = logging.getLogger(__name__)

try:
    # Python 3.5+
    from importlib.util import spec_from_file_location, module_from_spec
    from types import MethodType

    def import_module_from_file(inst, file_name, func_name):
        spec = spec_from_file_location('pyscada.scripting.user_script', file_name)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, func_name):
            return None
        return MethodType(getattr(mod, func_name), inst)

except:
    try:
        # Python 3.3, 3.4
        from importlib.machinery import SourceFileLoader
        from types import MethodType

        def import_module_from_file(inst, file_name, func_name):
            mod = SourceFileLoader('pyscada.scripting.user_script', file_name).load_module()
            if not hasattr(mod, func_name):
                return None
            return MethodType(getattr(mod, func_name), inst)
    except:
        try:
            # Python 2.7
            import imp
            from new import instancemethod

            def import_module_from_file(inst, file_name, func_name):
                mod = imp.load_source('pyscada.scripting.user_script', file_name)
                if not hasattr(mod,func_name):
                    return None
                return instancemethod(getattr(mod, func_name), inst, None)
        except:

            def import_module_from_file(inst, file_name):
                return None


class ScriptingProcess(BaseProcess):
    def __init__(self, dt=5, **kwargs):
        self.script_id = 0
        self.error_count = 0
        self.variables = {}
        self.script_file = None
        super(ScriptingProcess, self).__init__(dt=dt, **kwargs)
        self.script = import_module_from_file(self, self.script_file, 'script')
        self.startup = import_module_from_file(self, self.script_file, 'startup')
        self.shutdown = import_module_from_file(self, self.script_file, 'shutdown')
        self.data = {} # todo not implemented yet
        self._tmpdata = []

    def cov_handler(self,instance, timestamp, value, **kwargs):
        """

        :param instance:
        :param timestamp:
        :param value:
        :return:
        """
        self.data[instance.name] = [timestamp, value]

    def read_values_from_db(self, variable_names, time_from=None, time_to=None, mean_value_period=0,
                            no_mean_value=True, add_latest_value=True, query_first_value=True,
                            current_value_only=False):
        """
        read data from the database
        :param current_value_only:
        :param variable_names:
        :param time_from:
        :param time_to:
        :param mean_value_period:
        :param no_mean_value:
        :param add_latest_value:
        :param query_first_value:
        :return: list of numpy arrays
        """
        if time_from is None:
            time_from = time() - 60

        if time_to is None:
            time_to=time()

        variables = Variable.objects.filter(name__in=variable_names)
        """
        for variable in variables:
            if variable.name not in self.variables:
                self.variables[variable.name] = variable
        """
        data = RecordedData.objects.get_values_in_time_range(
            variable__in=variables,
            time_min=time_from,
            time_max=time_to,
            query_first_value=query_first_value,
            key_is_variable_name=True,
            blow_up=True,
            add_latest_value=add_latest_value,
            mean_value_period=mean_value_period if mean_value_period != 0 else 5.0,
            no_mean_value=True if mean_value_period != 0 else no_mean_value
        )
        if current_value_only:
            for key, item in data.items():
                data[key] = item[-1]
            return data

        for key, item in data.items():
            data[key] = np.asarray(item),

        return data

    def write_value_to_device(self, variable_name, value, time_start=None, user=None, blocking=False, timeout=60):
        """

        :param timeout:
        :param variable_name:
        :param value:
        :param time_start:
        :param user: instance of the writing user, default is None
        :param blocking: wait until write succeeded
        :return:
        """
        if time_start is None:
            time_start = time()

        if variable_name in self.variables:
            variable = self.variables[variable_name]
        else:
            variable = Variable.objects.filter(name=variable_name).first()
            self.variables[variable_name] = variable

        if not variable:
            # todo throw exception
            return False
        if not variable.writeable:
            # todo throw exception
            return False
        dwt = DeviceWriteTask(variable=variable, value=value, start=time_start, user=user)
        dwt.save()
        if blocking:
            timeout = max(time(), time_start) + timeout
            while timeout < time():
                dwt.refresh_from_db()
                if dwt.done():
                    return True
            return False
        else:
            return True

    def write_values_to_db(self, data):
        """
        :param data: dict with values
        :return:
        """
        if 'timevalues' in data:
            timevalues = data['timevalues']
        else:
            timevalues = None

        for variable_name, items in data.items():
            if variable_name in self.variables:
                variable = self.variables[variable_name]
            else:
                variable = Variable.objects.filter(name=variable_name).first()
                self.variables[variable_name] = variable
            for i in range(len(items)):
                if not variable:
                    continue
                if variable.update_value(items[i], time() if timevalues is None else timevalues[i]):
                    recorded_data_element = variable.create_recorded_data_element()
                    if recorded_data_element is not None:
                        self._tmpdata.append(recorded_data_element)

    def write_variable_property(self, variable_name, property_name, value, **kwargs):
        """
        creates or writes a variable property
        :param variable_name: name of the Variable the property belongs to
        :param property_name: name of the property
        :param value: value
        :param kwargs:
        :return: VariableProperty object
        """
        if variable_name in self.variables:
            variable = self.variables[variable_name]
        else:
            variable = Variable.objects.filter(name=variable_name).first()
        return VariableProperty.objects.update_or_create_property(variable=variable,name=property_name,value=value,
                                                                  **kwargs)

    def read_variable_property(self, variable_name, property_name, **kwargs):
        """
        reads the value from a variable property if existing or None
        :param variable_name: name of the Variable the property belongs to
        :param property_name: name of the property
        :param kwargs:
        :return: property value
        """
        if variable_name in self.variables:
            variable = self.variables[variable_name]
        else:
            variable = Variable.objects.filter(name=variable_name).first()
        if not variable:
            return None
        vp = VariableProperty.objects.get_property(variable=variable, name=property_name, **kwargs)
        if vp:
            return vp.value()
        return None

    def loop(self):
        """
        this is a script loop
        :return:
        """
        self._tmpdata = []  # delete old values
        try:
            if self.script is not None:
                self.script()
            self.error_count = 0  # reset error count
        except:
            self.error_count += 1
            logger.error('%s(%d), unhandled exception in script\n%s' % (self.label, getpid(), traceback.format_exc()))

        if self.error_count > 3:
            return 0, None

        if isinstance(self._tmpdata, list):
            if len(self._tmpdata) > 0:
                return 1, [self._tmpdata, ]

        return 1, None

    def init_process(self):
        """

        :return:
        """
        try:
            if self.startup is not None:
                self.startup()
        except:
            logger.error('%s(%d), unhandled exception in startup\n%s' % (self.label, getpid(), traceback.format_exc()))

    def cleanup(self):
        """

        :return:
        """
        try:
            if self.shutdown is not None:
                self.shutdown()
        except:
            logger.error('%s(%d), unhandled exception in shutdown\n%s' % (self.label, getpid(), traceback.format_exc()))
        # delete the background process entry
        BackgroundProcess.objects.filter(pk=self.process_id).delete()

    def script(self):
        """
        to be overwritten by the script
        :return:
        """
        pass

    def startup(self):
        """
        to be overwritten by the script
        :return:
        """
        pass

    def shutdown(self):
        """
        to be overwritten by the script
        :return:
        """
        pass


class MasterProcess(BaseProcess):
    """
    handle the registration of new script tasks, and monitor running script tasks
    """

    def __init__(self, dt=5, **kwargs):
        super(MasterProcess, self).__init__(dt=dt, **kwargs)
        self.SCRIPT_PROCESSES = []

    def init_process(self):
        for process in BackgroundProcess.objects.filter(parent_process__pk=self.process_id, done=False):
            try:
                kill(process.pid, 0)
            except OSError as e:
                if e.errno == errno.ESRCH:
                    process.delete()
                    continue
            logger.debug('process %d is alive' % process.pk)
            process.stop()

        # clean up
        BackgroundProcess.objects.filter(parent_process__pk=self.process_id, done=False).delete()

        for script_process in Script.objects.filter(active=True):
            bp = BackgroundProcess(label='pyscada.scripting.ScriptingProcess-%d' % script_process.pk,
                                   message='waiting..',
                                   enabled=True,
                                   parent_process_id=self.process_id,
                                   process_class='pyscada.scripting.worker.ScriptingProcess',
                                   process_class_kwargs=json.dumps({"script_id": script_process.pk,
                                                                    'script_file': script_process.script_file,
                                                                    'dt_set': script_process.interval}))
            bp.save()
            self.SCRIPT_PROCESSES.append({'id': bp.id,
                                          'script_id':script_process.pk,
                                          'failed': 0})

    def loop(self):
        """

        """
        # check if all modbus processes are running
        for script_process in self.SCRIPT_PROCESSES:
            try:
                BackgroundProcess.objects.get(pk=script_process['id'])
            except BackgroundProcess.DoesNotExist or BackgroundProcess.MultipleObjectsReturned:
                # Process is dead, spawn new instance
                if script_process['failed'] < 3:
                    script = Script.objects.get(pk=script_process['script_id'])
                    bp = BackgroundProcess(label='pyscada.scripting.ScriptingProcess-%d' % script.pk,
                                           message='waiting..',
                                           enabled=True,
                                           parent_process_id=self.process_id,
                                           process_class='pyscada.scripting.worker.ScriptingProcess',
                                           process_class_kwargs=json.dumps({"script_id": script.pk,
                                                                            'script_file': script.script_file,
                                                                            'dt_set': script.interval}))
                    bp.save()
                    script_process['id'] = bp.id
                    script_process['failed'] += 1
                else:
                    logger.error('process pyscada.scripting.user_script-%d failed more then 3 times' % script_process['script_id'])
            except:
                logger.debug('%s, unhandled exception\n%s' % (self.label, traceback.format_exc()))

        return 1, None

    def cleanup(self):
        # todo cleanup
        pass

    def restart(self):
        for script_process in self.SCRIPT_PROCESSES:
            try:
                bp = BackgroundProcess.objects.get(pk=script_process['id'])
                bp.restart()
            except:
                logger.debug('%s, unhandled exception\n%s' % (self.label, traceback.format_exc()))

        return False

