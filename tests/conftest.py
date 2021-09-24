"""Configuration file for our tests.

Here we create fixtures that are not directly required by test functions.
"""

import sys

import os

import pytest

import tables

from qtpy import QtWidgets

import vitables.vtapp
from vitables.preferences import vtconfig


class Launcher(object):
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setOrganizationDomain('vitables.org')
        self.app.setOrganizationName('ViTables')
        self.app.setApplicationName('ViTables')
        self.app.setApplicationVersion(vtconfig.getVersion())
        self.vtapp_object = vitables.vtapp.VTApp(keep_splash=False)
        self.gui = self.vtapp_object.gui


@pytest.fixture(scope='module')
def launcher():
    return Launcher()

@pytest.fixture(scope='module')
def h5file():
    if not os.path.exists('testfile.h5'):
        import create_testfile
    yield tables.open_file('testfile.h5', 'r')
    os.remove('testfile.h5')
