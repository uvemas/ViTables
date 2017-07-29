"""Configuration file for our tests.

Here we create fixtures that are not directly required by test functions.
"""

import sys

import pytest

from qtpy import QtWidgets

import vitables.vtapp


class Launcher(object):
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.vtapp_object = vitables.vtapp.VTApp(keep_splash=False)


@pytest.fixture(scope='module')
def launcher():
    return Launcher()
