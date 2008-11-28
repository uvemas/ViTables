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
#       $Id: vtInputBox.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""Here is defined the VTInputBox class.

Classes:

* VTInputBox(qt.QDialog)

Methods:

* __init__(self, header, current, label, caption, is_file=False)
* __tr(self, source, comment=None)
* addComponents(self, header, label, current)
* slotAccept(self)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import qt

import vitables.utils

class VTInputBox(qt.QDialog):
    """
    A customized QInpoutBox.getText dialog.

    The QInputDialog class doesn't provides validators.
    As a workaround we define our own input box.

    This is a helper class for other modules. It is called in the
    following cases: to enter new group names, rename nodes, 
    paste/drop nodes and save a file as a different one.
    """


    def __init__(self, header, current, label, caption, is_file=False):
        """
        The dialog contructor.

        Ctor add components, give them a layout and connect signals
        to slots.

        :Parameters:

        - `header an explanatory text
        - `label the label besides the text box
        - `current the initial content of the text box
        - `caption the dialog caption
        """

        # Makes the input box dialog and gives it a layout
        qt.QDialog.__init__(self, qt.qApp.mainWidget())
        qt.QVBoxLayout(self, 5, 11)
        self.setCaption(self.__tr(caption, 'A dialog caption.'))

        self.is_file = is_file

        # Main widgets
        self.value_le = qt.QLineEdit(self)
        self.ok_button = qt.QPushButton(self.__tr('&OK', 'A button label'), self)
        self.cancel_button = qt.QPushButton(self.__tr('&Cancel',
            'A button label'), self)
        self.addComponents(header, label, current)

        # Connects SIGNALs to SLOTs
        self.connect(self.ok_button, qt.SIGNAL('clicked()'), self.slotAccept)
        self.connect(self.cancel_button, qt.SIGNAL('clicked()'), qt.SLOT('reject()'))


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('VTInputBox', source, comment).latin1()


    def addComponents(self, header, label, current):
        """
        Adds components to the dialog.

        The dialog layout looks like this::

            root
                header
                label + textbox
                hspacer + OK + Cancel + hspacer

        :Parameters:

        - `header`: the question that the dialog will ask
        - `label`: the label besides the text box
        - `current`: the initial content of the text box
        """

        dlg_layout = self.layout()

        # FIRST ROW. A dialog purpose label
        header_label = qt.QLabel(self.__tr(header, 'A dialog label'), self)
        dlg_layout.addWidget(header_label)

        # SECOND ROW. New value: value
        h1_layout = qt.QHBoxLayout(dlg_layout, 5)
        value_label = qt.QLabel(self.__tr('%s', 'A text box label') % label, self)
        if self.is_file:
            regexp = qt.QRegExp("[a-zA-Z_]+[0-9a-zA-Z_]*\.(h5|hd5|hdf5)$")
        else:
            regexp = qt.QRegExp("[a-zA-Z_]+[0-9a-zA-Z_]*")
        v = qt.QRegExpValidator(self)
        v.setRegExp(regexp)
        self.value_le.setValidator(v)
        h1_layout.addWidget(value_label)
        h1_layout.addWidget(self.value_le)

        self.value_le.setText(current)
        self.value_le.selectAll()

        # THIRD ROW OK + Cancel
        # Horizontal stretchs will keep centered the OK and Cancel buttons
        h2_layout = qt.QHBoxLayout(dlg_layout, 5)

        # OK button
        # Cancel button
        h2_layout.addStretch(1)
        h2_layout.addWidget(self.ok_button)
        h2_layout.addWidget(self.cancel_button)
        h2_layout.addStretch(1)


    def slotAccept(self):
        """
        Checks the contents of text boxes and returns.

        This slot is executed when the user clicks the `OK` button.
        """

        value = self.value_le.text()
        self.newValue = value.latin1()
        self.accept()

