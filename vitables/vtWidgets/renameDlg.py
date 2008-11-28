# -*- coding: utf-8 -*-

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
#       $Id: renameDlg.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the RenameDlg class.

Classes:

* RenameDlg(qt.QDialog)

Methods:

* __init__(self, editing, data)
* __tr(self, source, comment=None)
* getCaption(self, editing_action)
* getLabels(self, editing_action, data)
* getActionButtonText(self, editing_action)
* addComponents(self)
* slotCheckNewName(self, current)
* slotOverwrite(self)
* slotRename(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import os.path
import qt

class RenameDlg(qt.QDialog):
    """
    Ask user help to solve a name problem.
    
    Some times naming problems appear when during file editing:

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


    def __init__(self, editing, data):
        """
        `data` always has format::

            [src_data, target_data, troubled_name]

        :Parameters:

        - `editing`: the editing action being done
        - `data`: the data tied to the editing action
        """

        # Makes the dialog and gives it a layout
        qt.QDialog.__init__(self, qt.qApp.mainWidget())
        qt.QVBoxLayout(self, 5, 11)

        # Sets dialog caption
        self.setCaption(self.getCaption(editing))

        self.troubled_name = data[-1]

        # The full path of the temporary database must be
        # considered in File Save As... operations
        if editing == 'save_as':
            self.tmp_db = data[1]
            self.target_directory = data[2]
        else:
            self.tmp_db = ""
            self.target_directory = ""

        # The result returned by this dialog will be contained in the
        # action dictionary. Its values can be:
        # If Overwrite --> True, troubled_name
        # If Rename --> False, new_name
        # If Cancel --> False, ''
        self.action = {'overwrite': False, 'new_nodename': ''}
        
        # Main widgets
        self.info_text = self.getLabels(editing, data)
        self.value_le = qt.QLineEdit(self)
        self.button_group = qt.QButtonGroup(3, qt.Qt.Horizontal, self)
        self.editing_button = qt.QPushButton(self.getActionButtonText(editing),
            self.button_group)
        self.overwrite_button = \
            qt.QPushButton(self.__tr('Overwrite', 'A button label'),
            self.button_group)
        self.cancel_button = qt.QPushButton(self.__tr('Cancel',
            'A button label'), self.button_group)

        # Connects SIGNALs to SLOTs
        self.connect(self.value_le, qt.SIGNAL('textChanged(const QString &)'),
            self.slotCheckNewName)
        self.connect(self.editing_button, qt.SIGNAL('clicked()'),
            self.slotRename)
        self.connect(self.overwrite_button, qt.SIGNAL('clicked()'),
            self.slotOverwrite)
        self.connect(self.cancel_button, qt.SIGNAL('clicked()'),
            qt.SLOT('reject()'))

        self.addComponents()
        self.value_le.selectAll()


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('RenameDlg', source, comment).latin1()


    def getCaption(self, editing_action):
        """
        Obtain the text to be displayed as dialog caption.

        The text depends on the action being executed.

        :Parameter editing_action: the editing action being done
        """

        if editing_action == "save_as":
            return self.__tr('File Save as: file already exists',
                'A dialog caption')
        elif editing_action == "create_group":
            return self.__tr('Creating a group: node already exists',
                'A dialog caption')
        elif editing_action == "paste_node":
            return self.__tr('Pasting a node: node already exists',
                'A dialog caption')
        elif editing_action == "move_node":
            return self.__tr('Moving a node: node already exists',
                'A dialog caption')
        elif editing_action == "rename_node":
            return self.__tr('Node renaming: name already in use',
                'A dialog caption')


    def getLabels(self, editing_action, data):
        """
        Obtain the text to be displayed in the dialog label.

        The text depends on the action being executed.

        :Parameters:

        - `editing_action`: the editing action being done
        - `data`: the data used to obtain the text
        """

        if editing_action == "save_as":
            return self.__tr("""Target directory: %s\n\n"""\
                """File name '%s' is already in use in that directory.\n""",
                'A dialog label') % \
                (data[2], self.troubled_name)
        elif editing_action == "create_group":
            return self.__tr("""File path: %s\n"""\
                """Parent group: %s\n\n"""\
                """Node name '%s' is already in use in that group.\n""",
                'A dialog label') % \
                (data[0], data[1], self.troubled_name)
        elif editing_action == "paste_node":
            return self.__tr("""Source file: %s\n"""\
                """Copied node: %s\n"""\
                """Destination file: %s\n"""\
                """Parent group: %s\n\n"""\
                """Node name '%s' is already in use in that group.\n""", 
                'A dialog label') % \
                (data[0], data[1], data[2], data[3], self.troubled_name)
        elif editing_action == "move_node":
            return self.__tr("""Source file: %s\n"""\
                """Moved node: %s\n"""\
                """Destination file: %s\n"""\
                """Parent group: %s\n\n """\
                """Node name '%s' is already in use in that group.\n""", 
                'A dialog label') % \
                (data[0], data[1], data[2], data[3], self.troubled_name)
        elif editing_action == "rename_node":
            return self.__tr("""Source file: %s\n"""\
                """Renamed node: %s\n\n"""\
                """New name '%s' is already in use.\n""", 
                'A dialog label') % \
                (data[1], os.path.join(data[2], data[0]), self.troubled_name)


    def getActionButtonText(self, editing_action):
        """
        Obtain the text to be displayed in the action button.

        The text depends on the action being executed.

        :Parameter editing_action: the editing action being done
        """

        if editing_action == "save_as":
            return self.__tr('Save', 'A button label')
        elif editing_action == "create_group":
            return self.__tr('Create', 'A button label')
        elif editing_action == "paste_node":
            return self.__tr('Paste', 'A button label')
        elif editing_action == "move_node":
            return self.__tr('Move', 'A button label')
        elif editing_action == "rename_node":
            return self.__tr('Rename', 'A button label')


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
        info = qt.QLabel(self.info_text, self)
        self.layout().addWidget(info)

        # SECOND ROW -- An input box
        # Blanks are not allowed. First character cannot be a digit
        newname_layout = qt.QHBoxLayout(self.layout(), 5)
        newname_layout.setMargin(11)
        value_label = qt.QLabel(self.__tr('New name:', 'A text box label'),
            self)
        newname_layout.addWidget(value_label)
        if self.tmp_db:
            regexp = qt.QRegExp("[a-zA-Z_]+[0-9a-zA-Z_]*(\.[0-9a-zA-Z_]+)?$")
        else:
            regexp = qt.QRegExp("[a-zA-Z_]+[0-9a-zA-Z_]*")
        validator = qt.QRegExpValidator(self)
        validator.setRegExp(regexp)
        self.value_le.setValidator(validator)
        self.value_le.setText(self.troubled_name)
        newname_layout.addWidget(self.value_le)

        # LAST ROW -- A group of  buttons
        self.button_group.setFrameStyle(qt.QFrame.NoFrame)

        # Rename button. ID=0
        self.editing_button.setEnabled(0)
        self.editing_button.setDefault(1)

        # Overwrite button. ID=1
        if self.troubled_name == '/':
            self.overwrite_button.setEnabled(0)

        # Cancel button. ID=2

        # Layout the buttons in such a way that they dont become wider
        # when the dialog is horizontally expanded
        buttons_layout = qt.QHBoxLayout(self.layout())
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.button_group)
        buttons_layout.addStretch(1)


    def slotCheckNewName(self, current):
        """
        Check the current name value.
        
        Every time that the text box content changes, this method is 
        asked to check if the new name and the original name differ.
        If so, the Rename is enabled and the Overwrite button is 
        disabled. If not, the Rename button is disabled and the 
        Overwrite button is enabled.

        :Parameter current: the value currently displayed in the text box
        """

        if not current.latin1():
            self.editing_button.setEnabled(0)
            self.overwrite_button.setEnabled(0)
        elif current.latin1() == self.troubled_name:
            self.editing_button.setEnabled(0)
            if os.path.join(self.target_directory, current.latin1()) != self.tmp_db:
                self.overwrite_button.setEnabled(1)
            else:
                self.overwrite_button.setEnabled(0)
        else:
            self.editing_button.setEnabled(1)
            self.overwrite_button.setEnabled(0)


    def slotOverwrite(self):
        """
        Set the new name and exit.

        When the Overwrite button is clicked the new name is saved and
        the dialog finishes.
        """

        self.action['overwrite'] = True
        self.action['new_nodename'] = self.troubled_name
        self.accept()


    def slotRename(self):
        """
        Set the new name and exit.

        When the Rename button is clicked the new name is saved and
        the dialog finishes.
        """

        # Validate the content of the text boxes
        validator = self.value_le.validator()
        nodename = self.value_le.text()
        state, ok = validator.validate(nodename, nodename.length())
        # If the content is not valid the dialog remains open
        if state != qt.QValidator.Acceptable:
            print self.__tr('The New name field contains a bad value',
                'A logger error message')
        else:
            self.action['overwrite'] = False
            self.action['new_nodename'] = nodename.latin1()
            self.accept()

