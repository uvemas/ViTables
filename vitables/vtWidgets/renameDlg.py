#!/usr/bin/env python
# -*- coding: utf-8 -*-


#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008, 2009 Vicent Mas. All rights reserved
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
Here is defined the RenameDlg class.

Classes:

* RenameDlg(QDialog)

Methods:

* __init__(self, name, pattern, info)
* __tr(self, source, comment=None)
* addComponents(self)
* slotCheckNewName(self, new_name)
* chooseAction(self, button)
* overwriteNode(self)
* renameNode(self)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class RenameDlg(QDialog):
    """
    Ask user for help when a name issue raises.
    
    Some times naming problems appear when during file editing:

    - when a file is being saved as a different one and its name is
      already being used by another file in the same directory
    - when a new group is being created and its name is already being
      used by other node in the destination group
    - when a node is being renamed and its new name is already being
      used by other node in the same group
    - when a node is being pasted/dropped and its name is already being
      used by other node in the destination group

    This dialog allows the user to solve the problem. Available options
    are:

    - rename the object in trouble
    - overwrite the existing object
    - cancel the editing action

    This dialog is also called for entering the initial name in the
    following cases:

    - group creation
    - node renaming

    In this cases the Overwrite button is not visible.
    """

    def __init__(self, name, pattern, info):
        """A customised QInputDialog.

        :Parameters:

        - `name`: the troubled name
        - `pattern`: a regular expression pattern that the name must match
        - `info`: dialog title and label
        """

        # Makes the dialog and gives it a layout
        QDialog.__init__(self, qApp.activeWindow())
        QVBoxLayout(self)

        # Sets dialog caption
        self.setWindowTitle(info[0])

        self.troubled_name = name
        self.pattern = QRegExp(pattern)
        self.cpattern = re.compile(pattern)
        self.info_text = info[1]

        # The result returned by this dialog will be contained in the
        # action dictionary. Its values can be:
        # If Overwrite --> True, troubled_name
        # If Rename --> False, new_name
        # If Cancel --> False, ''
        self.action = {'overwrite': False, 'new_name': ''}

        # Main widgets
        self.value_le = QLineEdit(self)
        self.rename_button = QPushButton(self.__tr('Rename', 
                                                    'A button label'), self)
        self.overwrite_button = QPushButton(self.__tr('Overwrite', 
                                                    'A button label'), self)
        self.cancel_button = QPushButton(self.__tr('Cancel',
                                                    'A button label'), self)

        self.buttons_box = QDialogButtonBox(Qt.Horizontal, self)
        self.buttons_box.addButton(self.rename_button, 
            QDialogButtonBox.AcceptRole)
        self.buttons_box.addButton(self.overwrite_button, 
            QDialogButtonBox.AcceptRole)
        self.buttons_box.addButton(self.cancel_button, 
            QDialogButtonBox.RejectRole)

        # Connects SIGNALs to SLOTs
        self.connect(self.value_le, 
            SIGNAL('textChanged(const QString)'),self.slotCheckNewName)
        self.connect(self.buttons_box, SIGNAL('clicked(QAbstractButton *)'), 
            self.chooseAction)
        self.connect(self.buttons_box, SIGNAL('rejected()'),
            SLOT('reject()'))

        self.addComponents()
        self.value_le.selectAll()

        # Make sure that buttons are in the proper activation state
        self.value_le.emit(SIGNAL('textChanged(const QString)'), 
            (self.value_le.text()))


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate('RenameDlg', source, comment))


    def addComponents(self):
        """
        Adds components to the dialog.

        The dialog layout looks like this::

            root
                label_text
                label + textbox
                Rename + Overwrite + Cancel
        """

        # FIRST ROW -- An informative label
        info = QLabel(self.info_text, self)
        self.layout().addWidget(info)

        # SECOND ROW -- An input box
        # Blanks are not allowed. First character cannot be a digit
        newname_layout = QHBoxLayout()
        newname_layout.setSpacing(5)
        value_label = QLabel(self.__tr('New name:', 'A text box label'),
            self)
        newname_layout.addWidget(value_label)
        validator = QRegExpValidator(self)
        validator.setRegExp(self.pattern)
        self.value_le.setValidator(validator)
        self.value_le.setText(self.troubled_name)
        newname_layout.addWidget(self.value_le)
        self.layout().addLayout(newname_layout)

        # LAST ROW -- A set of  buttons
        self.rename_button.setDefault(1)
        self.layout().addWidget(self.buttons_box)


    def slotCheckNewName(self, new_name):
        """
        Check the new name value.

        Every time that the text box content changes, this method is 
        asked to check if the new name and the original name differ.
        Four cases can arise:

            1) the new name is empty
            2) the new name and the current nodename are the same
            3) the new name and the current name differ and the new name
              is not being used by a sibling node
            4) the new name and the current name differ and the new name
              is being used by a sibling node

        In cases 1) and 2) the new name is not valid, the Rename and Overwrite
        buttons are both disabled.
        In case 3) the Rename button is enabled and the Overwrite one is not.
        In case 4) the Overwrite button is enabled but the Rename one is not.

        Beware that case 2) can appear only during a node renaming operation or
        during a file Save As operation (not when creating a new group or
        pasting/dropping a node)

        :Parameter new_name: the value currently displayed in the text box
        """

        # If the new name and the current nodename are the same then the
        # group 1 of the pattern is matched
        new_name = unicode(new_name)
        result = self.cpattern.search(new_name)
        if (result == None) or \
            ((result != None) and (result.lastindex == 1)) or \
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


    def chooseAction(self, button):
        """Perform the action specified by the clicked button."""

        if button == self.rename_button:
            self.renameNode()
        elif button == self.overwrite_button:
            self.overwriteNode()


    def overwriteNode(self):
        """
        Set the new name and exit.

        When the Overwrite button is clicked the new name is saved and
        the dialog finishes.
        """

        self.action['overwrite'] = True
        self.action['new_name'] = self.troubled_name
        self.accept()


    def renameNode(self):
        """
        Set the new name and exit.

        When the Rename button is clicked the new name is saved and
        the dialog finishes.
        """

        new_name = unicode(self.value_le.text())
        self.action['overwrite'] = False
        self.action['new_name'] = new_name
        self.accept()
