# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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
Here is defined the InputNodeName class.

Classes:

* InputNodeName(QtGui.QDialog, Ui_InputNodenameDialog)

Methods:

* __init__(self, title, info, action)
* slotCheckNewName(self, current)
* slotAccept(self)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'InputNodeName'

import os.path

from PyQt4 import QtCore, QtGui
from PyQt4.uic import loadUiType

# This method of the PyQt4.uic module allows for dinamically loading user 
# interfaces created by QtDesigner. See the PyQt4 Reference Guide for more
# info.
Ui_InputNodenameDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__),'nodename_dlg.ui'))[0]



class InputNodeName(QtGui.QDialog, Ui_InputNodenameDialog):
    """
    Dialog for interactively entering a name for a given node.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This dialog is called when a new group is being created and also when
    a node of any kind is being renamed.

    Regular Qt class QInputDialog is not used because, at least apparently, 
    it doesn't provide a way for customizing buttons text.
    """

    def __init__(self, title, info, action):
        """A customised QInputDialog.

        :Parameters:

        - `title`: the dialog title
        - `info`: information to be displayed in the dialog
        - `action`: string with the editing action to be done, Create or Rename
        """

        # Makes the dialog and gives it a layout
        QtGui.QDialog.__init__(self, QtGui.qApp.activeWindow())
        self.setupUi(self)

        # Set dialog caption and label with general info
        self.setWindowTitle(title)
        self.general_info.setText(info)

        # The Create/Rename button
        self.edit_button = self.buttons_box.addButton(action, 
            QtGui.QDialogButtonBox.AcceptRole)

        # Setup a validator for checking the entered node name
        validator = QtGui.QRegExpValidator(self)
        pattern = QtCore.QRegExp("[a-zA-Z_]+[0-9a-zA-Z_ ]*")
        validator.setRegExp(pattern)
        self.value_le.setValidator(validator)

        # Connects SIGNALs to SLOTs
        self.connect(self.value_le, 
            QtCore.SIGNAL('textChanged(const QString)'),self.slotCheckName)
        self.connect(self.buttons_box, QtCore.SIGNAL('accepted()'),
            self.slotAccept)
        self.connect(self.buttons_box, QtCore.SIGNAL('rejected()'),
            QtCore.SLOT('reject()'))

        self.value_le.selectAll()

        # Make sure that buttons are in the proper activation state
        self.value_le.emit(QtCore.SIGNAL('textChanged(const QString)'), 
            (self.value_le.text()))


    def slotCheckName(self, current):
        """
        Check the current name value.

        The state of the Create button depends on the passed string. If
        it is empty then the button is disabled. Otherwhise it is enabled.

        :Parameter current: the value currently displayed in the text box
        """

        if current.isEmpty():
            self.edit_button.setEnabled(0)
        else:
            self.edit_button.setEnabled(1)


    def slotAccept(self):
        """Save the entered group name and hide the dialog.
        """

        self.node_name = unicode(self.value_le.text())
        self.accept()
