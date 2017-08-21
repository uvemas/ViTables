#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2017 Vicent Mas. All rights reserved
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#       Author:  Vicent Mas - vmas@vitables.org

"""
This module provides a dialog for renaming nodes of the tree of databases view.

The dialog is raised when a new group node is created and when an existing node
is being renamed.
"""

import os.path

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.uic import loadUiType

import vitables.utils

__docformat__ = 'restructuredtext'

# This method of the PyQt5.uic module allows for dinamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_InputNodenameDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__), 'nodename_dlg.ui'))[0]


class InputNodeName(QtWidgets.QDialog, Ui_InputNodenameDialog):
    """
    Dialog for interactively entering a name for a given node.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This dialog is called when a new group is being created and also when
    a node of any kind is being renamed.

    Regular Qt class QInputDialog is not used because, at least apparently,
    it doesn't provide a way for customizing buttons text.

    :Parameters:

    - `title`: the dialog title
    - `info`: information to be displayed in the dialog
    - `action`: string with the editing action to be done, Create or Rename
    """

    def __init__(self, title, info, action, default_value=None):
        """A customised `QInputDialog`.
        """

        vtapp = vitables.utils.getVTApp()
        # Makes the dialog and gives it a layout
        super(InputNodeName, self).__init__(vtapp.gui)
        self.setupUi(self)

        # Set dialog caption and label with general info
        self.setWindowTitle(title)
        self.generalInfo.setText(info)

        # The Create/Rename button
        self.edit_button = self.buttonsBox.addButton(
            action, QtWidgets.QDialogButtonBox.AcceptRole)

        # Setup a validator for checking the entered node name
        validator = QtGui.QRegExpValidator(self)
        pattern = QtCore.QRegExp("[a-zA-Z_]+[0-9a-zA-Z_ ]*")
        validator.setRegExp(pattern)
        self.valueLE.setValidator(validator)

        if default_value:
            self.valueLE.setText(default_value)
            
        # Make sure that buttons are in the proper activation state
        self.valueLE.textChanged.emit(self.valueLE.text())

    @QtCore.Slot("QString", name="on_valueLE_textChanged")
    def checkName(self, current):
        """
        Check the current name value.

        The state of the `Create` button depends on the passed string. If
        it is empty then the button is disabled. Otherwise it is enabled.

        :Parameter current: the value currently displayed in the text box
        """

        if current == '':
            self.edit_button.setEnabled(0)
        else:
            self.edit_button.setEnabled(1)

    @QtCore.Slot(name="on_buttonsBox_accepted")
    def saveName(self):
        """Slot for saving the entered name and closing the dialog.
        """

        self.node_name = self.valueLE.text()
        self.accept()
