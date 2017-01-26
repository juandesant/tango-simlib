import os
import time
import logging
import unittest
import shutil
import tempfile
import subprocess

import PyTango
import pkg_resources

from tango_simlib.sim_test_interface import SimControl
from tango_simlib.testutils import ClassCleanupUnittestMixin
from tango_simlib import tango_sim_generator, sim_xmi_parser, helper_module


MODULE_LOGGER = logging.getLogger(__name__)


class test_TangoSimGenDeviceIntegration(ClassCleanupUnittestMixin, unittest.TestCase):

    longMessage = True

    @classmethod
    def setUpClassWithCleanup(cls):
        cls.port = helper_module.get_port()
        cls.data_descr_file = [pkg_resources.resource_filename(
            'tango_simlib.tests', 'weather_sim.xmi')]
        cls.temp_dir = tempfile.mkdtemp()
        cls.sim_device_class = tango_sim_generator.get_device_class(cls.data_descr_file)
        device_name = 'test/nodb/tangodeviceserver'
        server_name = 'weather_ds'
        server_instance = 'test'
        database_filename = '%s/%s_tango.db' % (cls.temp_dir, server_name)
        sim_device_prop = dict(sim_data_description_file=cls.data_descr_file[0])
        sim_test_device_prop = dict(model_key=device_name)
        tango_sim_generator.generate_device_server(
                server_name, cls.data_descr_file, cls.temp_dir)
        helper_module.append_device_to_db_file(
                server_name, server_instance, device_name,
                database_filename, cls.sim_device_class, sim_device_prop)
        helper_module.append_device_to_db_file(
                server_name, server_instance, '%scontrol' % device_name,
                database_filename, '%sSimControl' % cls.sim_device_class,
                sim_test_device_prop)
        cls.sub_proc = subprocess.Popen('python %s/%s.py %s -file=%s '
                                        '-ORBendPoint giop:tcp::%s' % (
                                           cls.temp_dir, server_name,
                                           server_instance, database_filename,
                                           cls.port), shell=True)
        # Note that the connection request must be delayed
        # by atleast 1000 ms of device server start up.
        time.sleep(1)
        cls.sim_device = PyTango.DeviceProxy(
                'localhost:%s/test/nodb/tangodeviceserver#dbase=no' % cls.port)
        cls.sim_control_device = PyTango.DeviceProxy(
                'localhost:%s/test/nodb/tangodeviceservercontrol#dbase=no' % cls.port)
        cls.addCleanupClass(subprocess.call, 'fuser -k %s/tcp' % cls.port, shell=True)
        cls.addCleanupClass(shutil.rmtree, cls.temp_dir)

    def setUp(self):
        super(test_TangoSimGenDeviceIntegration, self).setUp()
        self.xmi_parser = sim_xmi_parser.XmiParser()
        self.xmi_parser.parse(self.data_descr_file[0])
        self.expected_model = tango_sim_generator.configure_device_model(
                self.data_descr_file)

    def test_device_attribute_list(self):
        """ Testing whether the attributes specified in the POGO generated xmi file
        are added to the TANGO device
        """
        attributes = set(self.sim_device.get_attribute_list())
        expected_attributes = []
        default_attributes = helper_module.DEFAULT_TANGO_DEVICE_ATTRIBUTES
        for attribute_data in self.xmi_parser.device_attributes:
            expected_attributes.append(attribute_data['dynamicAttributes']['name'])
        self.assertEqual(set(expected_attributes), attributes - default_attributes,
                         "Actual tango device attribute list differs from expected "
                         "list!")

    def test_device_command_list(self):
        """Testing whether commands are defined on the device as expected
        """
        actual_device_commands = set(self.sim_device.get_command_list()) - {'Init'}
        expected_command_list = set(self.xmi_parser.get_reformatted_cmd_metadata().keys())
        self.assertEquals(actual_device_commands, expected_command_list,
                          "The commands specified in the xmi file are not present in"
                          " the device")

    def test_sim_control_attribute_list(self):
        implemented_attr = helper_module.SIM_CONTROL_ADDITIONAL_IMPLEMENTED_ATTR

    def test_sim_control_quantities(self):
        attributes = set(self.sim_control_device.get_attribute_list())

    def test_sim_control_change_device_attribute(self):
        pass
