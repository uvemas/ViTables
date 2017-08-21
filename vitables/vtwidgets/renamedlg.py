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
This module provides a dialog for solving node renaming issues on the tree of
databases view.

Some times naming problems appear when the tree is being edited:

  - when a file is being saved as a different one and its name is
    already being used by another file in the same directory
  - when a new group is being created and its name is already being
    used by other node in the destination group
  - when a node is being renamed and its new name is already being
    used by other node in the same group
  - when a node is being pasted/dropped and its name is already being
    used by other node in the destination group

This dialog allows the user to solve the problem. Available options are:

  - rename the object in trouble
  - overwrite the existing object
  - cancel the editing action

"""

import os.path
import re

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from qtpy.uic import loadUiType

import vitables.utils

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
# This method of the PyQt5.uic module allows for dinamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_RenameNodeDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__), 'rename_dlg.ui'))[0]


class RenameDlg(QtWidgets.QDialog, Ui_RenameNodeDialog):
    """
    Ask user for help when a name issue raises.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)


    Regular Qt class `QInputDialog` is not used because, at least apparently,
    it doesn't provide a way for customizing buttons text.

    This dialog allows the user to solve naming issues. Available options
    are:

      - rename the object in trouble
      - overwrite the existing object
      - cancel the editing action

    :Parameters:

    - `name`: the troubled name
    - `pattern`: a regular expression pattern that the name must match
    - `info`: dialog title and label
    """

    def __init__(self, name, pattern, info):
        """A customised `QInputDialog`.
        """

        vtapp = vitables.utils.getVTApp()
        # Makes the dialog and gives it a layout
        super(RenameDlg, self).__init__(vtapp.gui)
        self.setupUi(self)

        # Sets dialog caption
        self.setWindowTitle(info[0])
        self.generalInfo.setText(info[1])

        self.troubled_name = name
        self.cpattern = re.compile(pattern)

        # The result returned by this dialog will be contained in the
        # action dictionary. Its values can be:
        # If Overwrite --> True, troubled_name
        # If Rename --> False, new_name
        # If Cancel --> False, ''
        self.action = {'overwrite': False, 'new_name': ''}

        # The dialog buttons: Rename, Overwrite and Cancel
        self.overwrite_button = self.buttonsBox.addButton(
            translate('RenameDlg', 'Overwrite', 'A button label'),
            QtWidgets.QDialogButtonBox.AcceptRole)
        self.rename_button = self.buttonsBox.addButton(
            translate('RenameDlg', 'Rename', 'A button label'),
            QtWidgets.QDialogButtonBox.AcceptRole)
        self.rename_button.setDefault(1)
        self.cancel_button = self.buttonsBox.button(
            QtWidgets.QDialogButtonBox.Cancel)

        # Setup a validator for checking the entered node name
        validator = QtGui.QRegExpValidator(self)
        qt_pattern = QtCore.QRegExp(pattern)
        validator.setRegExp(qt_pattern)
        self.valueLE.setValidator(validator)
        self.valueLE.setText(self.troubled_name)

        self.valueLE.selectAll()

        # Make sure that buttons are in the proper activation state
        self.valueLE.textChanged.emit(self.valueLE.text())

    @QtCore.Slot('QString', name="on_valueLE_textChanged")
    def checkName(self, new_name):
        """
        Check the new name value.

        Every time that the text box content changes, this method is
        asked to check if the new name and the original name differ.
        Four cases can occur:

            1) the new name is empty
            2) the new name and the current nodename are the same
            3) the new name and the current name differ and the new name
               is not being used by a sibling node
            4) the new name and the current name differ and the new name
               is being used by a sibling node

        In cases 1) and 2) the new name is not valid, the `Rename` and
        `Overwrite` buttons are both disabled.
        In case 3) the `Rename` button is enabled and the `Overwrite` one is
        not. In case 4) the `Overwrite` button is enabled but the `Rename` one
        is not.

        Beware that case 2) can appear only during a node renaming operation or
        during a file `Save As...` operation (not when creating a new group or
        pasting/dropping a node)

        :Parameter new_name: the value currently displayed in the text box
        """

        # If the new name and the current nodename are the same then the
        # group 1 of the pattern is matched
        result = self.cpattern.search(new_name)
        if (result is None) or \
                ((result is not None) and (result.lastindex == 1)) or \
                (not new_name):
            self.rename_button.setEnabled(0)
            self.overwrite_button.setEnabled(0)
        elif new_name == self.troubled_name:
            self.rename_button.setEnabled(0)
            if self.troubled_name == '/':
                self.overwrite_button.setEnabled(0)
            else:
                self.overwrite_button.setEnabled(1)
        else:
            self.rename_button.setEnabled(1)
            self.overwrite_button.setEnabled(0)

    @QtCore.Slot("QAbstractButton *", name="on_buttonsBox_clicked")
    def executeAction(self, button):
        """Execute the action specified by the clicked button.

        :Parameter button: the clicked button (`Rename` or `Overwrite`)
        """

        if button == self.rename_button:
            self.rename_node()
        elif button == self.overwrite_button:
            self.overwriteNode()

    def overwriteNode(self):
        """
        Set the new name and exit.

        When the `Overwrite` button is clicked the new name is saved and
        the dialog finishes.
        """

        self.action['overwrite'] = True
        self.action['new_name'] = self.troubled_name
        self.accept()

    def rename_node(self):
        """
        Set the new name and exit.

        When the `Rename` button is clicked the new name is saved and
        the dialog finishes.
        """

        new_name = self.valueLE.text()
        self.action['overwrite'] = False
        self.action['new_name'] = new_name
        self.accept()
