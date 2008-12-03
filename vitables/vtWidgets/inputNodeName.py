# -*- coding: utf-8 -*-
#!/usr/bin/env python


########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008 Vicent Mas. All rights reserved
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
#
#       $Source$
#       $Id: inputNodeName.py 1069 2008-10-13 20:02:30Z vmas $
#
########################################################################

"""
Here is defined the InputNodeName class.

Classes:

* InputNodeName(QtGui.QDialog)

Methods:

* __init__(self, parent, pattern, info)
* __tr(self, source, comment=None)
* addComponents(self)
* slotCheckNewName(self, current)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

class InputNodeName(QtGui.QDialog):
    """
    Dialog for interactively entering a name for a given node.
    
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
        - `action`: the editing action to be done, Create or Rename
        """

        # Makes the dialog and gives it a layout
        QtGui.QDialog.__init__(self, QtGui.qApp.activeWindow())
        QtGui.QVBoxLayout(self)

        # Sets dialog caption
        self.setWindowTitle(title)

        self.info = info

        # Main widgets
        self.value_le = QtGui.QLineEdit(self)

        self.edit_button = QtGui.QPushButton(action, self)
        self.cancel_button = \
            QtGui.QPushButton(self.__tr('Cancel', 'A button label'), self)

        self.buttons_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.buttons_box.addButton(self.edit_button, 
            QtGui.QDialogButtonBox.AcceptRole)
        self.buttons_box.addButton(self.cancel_button, 
            QtGui.QDialogButtonBox.RejectRole)

        # Connects SIGNALs to SLOTs
        self.connect(self.value_le, 
            QtCore.SIGNAL('textChanged(const QString)'),self.slotCheckName)
        self.connect(self.buttons_box, QtCore.SIGNAL('accepted()'),
            self.slotAccept)
        self.connect(self.buttons_box, QtCore.SIGNAL('rejected()'),
            QtCore.SLOT('reject()'))

        self.addComponents()
        self.value_le.selectAll()

        # Make sure that buttons are in the proper activation state
        self.value_le.emit(QtCore.SIGNAL('textChanged(const QString)'), (self.value_le.text()))

    def __tr(self, source, comment=None):
        """Translate method."""
        return str(QtGui.qApp.translate('InputNodeName', source, comment))

    def addComponents(self):
        """
        Adds components to the dialog.

        The dialog layout looks like this::

            root
                label_text
                label + textbox
                Create + Cancel
        """

        # FIRST ROW -- An informative label
        info = QtGui.QLabel(self.info, self)
        self.layout().addWidget(info)

        # SECOND ROW -- An input box
        # Blanks are not allowed. First character cannot be a digit
        name_layout = QtGui.QHBoxLayout()
        name_layout.setSpacing(5)
        value_label = QtGui.QLabel(self.__tr('Node name:', 'A text box label'),
            self)
        name_layout.addWidget(value_label)
        validator = QtGui.QRegExpValidator(self)
        pattern = QtCore.QRegExp("[a-zA-Z_]+[0-9a-zA-Z_ ]*")
        validator.setRegExp(pattern)
        self.value_le.setValidator(validator)
        name_layout.addWidget(self.value_le)
        self.layout().addLayout(name_layout)

        # LAST ROW -- A set of  buttons
        self.layout().addWidget(self.buttons_box)


    def slotCheckName(self, current):
        """
        Check the current name value.

        The state of the Create button depends on the passed string. If
        it is empty then the button is disabled. Otherwhise it is enabled.

        :Parameter current: the value currently displayed in the text box
        """

        if not str(current):
            self.edit_button.setEnabled(0)
        else:
            self.edit_button.setEnabled(1)

    def slotAccept(self):
        """Save the entered group name and hide the dialog.
        """

        self.node_name = unicode(self.value_le.text())
        self.accept()
