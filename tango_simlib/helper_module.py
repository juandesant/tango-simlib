import os
import sys
import socket

from PyTango import Database
from PyTango.server import command


DEFAULT_TANGO_DEVICE_COMMANDS = frozenset(['State', 'Status', 'Init'])
DEFAULT_TANGO_DEVICE_ATTRIBUTES = frozenset(['State', 'Status', 'AttributesNotAdded',
                                             'NumAttributesNotAdded'])
SIM_CONTROL_ADDITIONAL_IMPLEMENTED_ATTR = set([
    'Status',            # Tango library attribute
    'State',             # Tango library attribute
    'attribute_name',    # Attribute indentifier for attribute to be controlled
    'pause_active'       # Flag for pausing the model updates
    ])

# Mandatory parameters required to create a well configure Tango attribute.
DEFAULT_TANGO_ATTRIBUTE_PARAMETER_TEMPLATE = {
    'abs_change': '',
    'archive_abs_change': '',
    'archive_period': '',
    'archive_rel_change': '',
    'data_format': '',
    'format': '',
    'data_type': '',
    'delta_t': '',
    'delta_val': '',
    'description': '',
    'display_level': '',
    'enum_lables': [],
    'event_period': '',
    'label': '',
    'max_alarm': '',
    'max_warning': '',
    'max_dim_x': '',
    'max_dim_y': '',
    'max_value': '',
    'min_alarm': '',
    'min_value': '',
    'min_warning': '',
    'name': '',
    'period': '',
    'rel_change': '',
    'unit': '',
    'update_period': '',
    'writable': ''
}

TANGO_NOT_SPECIFIED_PROPS = ['Not specified', 'No display unit', 'No standard unit']

POGO_USER_DEFAULT_CMD_PROP_MAP = {
        'name': 'name',
        'arginDescription': 'doc_in',
        'arginType': 'dtype_in',
        'argoutDescription': 'doc_out',
        'argoutType': 'dtype_out'}

def get_server_name():
    """Gets the TANGO server name from the command line arguments

    Returns
    -------
    server_name : str
        tango device server name

    Note
    ====
    Extract the Tango server_name or equivalent executable
    (i.e.sim_xmi_parser.py -> sim_xmi_parser or
    /usr/local/bin/mkat-tango-katcpdevice2tango-DS ->
    mkat-tango-katcpdevice2tango-DS) from the command line
    arguments passed, where sys.argv[1] is the server instance.

    """
    executable_name = os.path.split(sys.argv[0])[-1].split('.')[0]
    server_name = executable_name + '/' + sys.argv[1]
    return server_name

def append_device_to_db_file(server, instance, device, db_file_name,
                             tangoclass=None, properties={}):
    """Generate a database file corresponding to the given arguments."""
    if not tangoclass:
        tangoclass = server
    # Open the file
    with open(db_file_name, 'a') as f:
        f.write("/".join((server, instance, "DEVICE", tangoclass)))
        f.write(': "' + device + '"\n')
    # Create database
    db = Database(db_file_name)
    # Patched the property dict to avoid a PyTango bug
    patched = dict((key, value if value != '' else ' ')
                   for key, value in properties.items())
    # Write properties
    db.put_device_property(device, patched)
    return db

def get_port():
    sock = socket.socket()
    sock.bind(('', 0))
    res = sock.getsockname()[1]
    del sock
    return res

def get_host_address():
    host_name = socket.gethostname()
    return host_name

def generate_cmd_handler(model, action_name, action_handler):
        def cmd_handler(tango_device, input_parameters=None):
            return action_handler(tango_dev=tango_device, data_input=input_parameters)

        cmd_handler.__name__ = action_name
        cmd_info_copy = model.sim_actions_meta[action_name].copy()
        # Delete all the keys that are not part of the Tango command parameters.
        cmd_info_copy.pop('name')
        tango_cmd_prop = POGO_USER_DEFAULT_CMD_PROP_MAP.values()
        for prop_key in model.sim_actions_meta[action_name]:
            if prop_key not in tango_cmd_prop:
                MODULE_LOGGER.info(
                    "Warning! Property %s is not a tango command prop", prop_key)
                cmd_info_copy.pop(prop_key)
        """
        The command method signature:
        command(f=None, dtype_in=None, dformat_in=None, doc_in="",
                dtype_out=None, dformat_out=None, doc_out="", green_mode=None)
        """
        return command(f=cmd_handler, **cmd_info_copy)