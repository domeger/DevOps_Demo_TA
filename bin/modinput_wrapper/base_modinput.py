# encoding = utf-8
import importlib
import copy

from tab_splunklib import modularinput as smi
from tab_splunktalib.common.log import Logs

class BaseModInput(smi.Script):
    '''
    This is a modular input wrapper, which provides some helper
    functions to read the paramters from setup pages and the arguments
    from input definition
    '''

    def __init__(self, app_namespace, input_name):
        super(BaseModInput, self).__init__()
        self._canceled = False
        self.input_name = None
        self.input_args = {}
        self.namespace = app_namespace
        self.logger_name = "modinput_" + input_name
        self.logger = Logs().get_logger(self.logger_name)
        # try to load the setup util module
        self.setup_util_module = None
        self.setup_util = None
        try:
            self.setup_util_module = importlib.import_module(self.namespace +
             "_setup_util")
        except ImportError as ie:
            self.logger.error("Can not import package:" + self.namespace + "_setup_util")

    def log_error(self, msg):
        self.logger.error(msg)

    def log_debug(self, msg):
        self.logger.debug(msg)

    def log_info(self, msg):
        self.logger.info(msg)

    def get_proxy(self):
        ''' if the proxy setting is set. return a dict like
        {
        proxy_url: ... ,
        proxy_port: ... ,
        proxy_username: ... ,
        proxy_password: ... ,
        proxy_type: ... ,
        proxy_rdns: ...
        }
        '''
        if self.setup_util:
            return self.setup_util.get_proxy_settings()
        else:
            return None

    def get_global_setting(self, var_name):
        if self.setup_util:
            return self.setup_util.get_customized_setting(var_name)
        else:
            return None

    def get_user_credential(self, username):
        '''
        if the username exists, return
        {
            "username": username,
            "password": credential
        }
        '''
        if self.setup_util:
            return self.setup_util.get_credential_account(username)
        else:
            return None

    def get_log_level(self):
        if self.setup_util:
            return self.setup_util.get_log_level()
        else:
            return None

    def parse_input_args(self, inputs):
        raise NotImplemented()

    def new_event(self, data, time=None, host=None, index=None, source=None, sourcetype=None, done=True, unbroken=True):
        '''
        :param data: ``string``, the event's text.
        :param time: ``float``, time in seconds, including up to 3 decimal places to represent milliseconds.
        :param host: ``string``, the event's host, ex: localhost.
        :param index: ``string``, the index this event is specified to write to, or None if default index.
        :param source: ``string``, the source of this event, or None to have Splunk guess.
        :param sourcetype: ``string``, source type currently set on this event, or None to have Splunk guess.
        :param done: ``boolean``, is this a complete ``Event``? False if an ``Event`` fragment.
        :param unbroken: ``boolean``, Is this event completely encapsulated in this ``Event`` object?
        '''
        return smi.Event(data = data, time = time, host = host, index = index,
        source = source, sourcetype=sourcetype, done=done, unbroken=unbroken)


    def stream_events(self, inputs, ew):
        '''
        implement the tab_splunklib modular input
        preprocess the input args
        '''
        self.parse_input_args(copy.deepcopy(inputs))
        if self.setup_util_module:
            uri = self._input_definition.metadata["server_uri"]
            session_key = self._input_definition.metadata['session_key']
            self.setup_util = self.setup_util_module.Setup_Util(uri, session_key, self.logger)
            self.logger.setLevel(self.setup_util.get_log_level())

        self.collect_events(inputs, ew)

    def collect_events(self, inputs, event_writer):
        '''
        this method should be implemented in subclass
        '''
        raise NotImplemented()

    def get_input_name(self):
        '''
        get input names, if it is single instance modinput, return the name
        it it is multi instance modinput, return a list of names?
        This needs to be check!
        '''
        raise NotImplemented()

    def get_arg(self, arg_name, input_name=None):
        raise NotImplemented()

    def get_output_index(self, input_name=None):
        return self.get_arg('index', input_name)

    def get_sourcetype(self, input_name=None):
        return self.get_arg('sourcetype', input_name)


class SingleInstanceModInput(BaseModInput):
    def __init__(self, app_namespace, input_name):
        super(SingleInstanceModInput, self).__init__(app_namespace, input_name)

    def parse_input_args(self, inputs):
        # the single instance modinput just has one sections
        self.input_name, self.input_args = inputs.inputs.popitem()

    def get_input_name(self):
        return self.input_name

    def get_arg(self, arg_name, input_name=None):
        return self.input_args.get(arg_name, None)
