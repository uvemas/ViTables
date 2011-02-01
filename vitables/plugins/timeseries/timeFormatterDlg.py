# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2011 Vicent Mas. All rights reserved
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

__docformat__ = 'restructuredtext'

import os.path
import ConfigParser
import datetime

from PyQt4 import QtGui
from PyQt4.uic import loadUiType

import vitables.utils

# This method of the PyQt4.uic module allows for dinamically loading user 
# interfaces created by QtDesigner. See the PyQt4 Reference Guide for more
# info.
Ui_TimeFormatterDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__), 
    'timeformatter_dlg.ui'))[0]



class TimeFormatterDlg(QtGui.QDialog, Ui_TimeFormatterDialog):
    """
    Dialog for interactively formatting scikits.timeseries time series.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This dialog is called when the Configure button is clicked in Time Series
    entry of the Plugins menu.

    :Parameters:

    - `title`: the dialog title
    - `info`: information to be displayed in the dialog
    - `action`: string with the editing action to be done, Create or Rename
    """

    def __init__(self):
        """A dialog for customising time formats.
        """

        vtapp = vitables.utils.getVTApp()
        # Makes the dialog and gives it a layout
        super(TimeFormatterDlg, self).__init__(vtapp.gui)
        self.setupUi(self)

        config = ConfigParser.RawConfigParser()
        def_tformat = '%c' 
        try:
            config.read(\
                os.path.join(os.path.dirname(__file__), u'time_format.ini'))
            self.tformat = config.get('Timeseries', 'strftime')
        except (IOError, ConfigParser.Error):
            self.tformat = def_tformat

        self.tformat_editor.setText(self.tformat)
        today = datetime.datetime.today().strftime(self.tformat)
        self.today_label.setText(today)

        ok_button = self.button_box.button(QtGui.QDialogButtonBox.Ok)
        apply_button = self.button_box.button(QtGui.QDialogButtonBox.Apply)
        ok_button.clicked.connect(self.saveFormat)
        apply_button.clicked.connect(self.checkFormat)

        self.show()


    def checkFormat(self):
        """
        Check the current time format.

        The time format currently entered in the line editor is applied to the
        sample label showing the today date. If the result is that expected by
        user then she can click safely the OK button. Otherwhise she should try
        another time format.
        """

        today = datetime.datetime.today().strftime(self.tformat_editor.text())
        self.today_label.clear()
        self.today_label.setText(today)




    def saveFormat(self):
        """Slot for saving the entered time format and closing the dialog.
        """

        config = ConfigParser.RawConfigParser()
        filename = os.path.join(os.path.dirname(__file__), u'time_format.ini')
        config.read(filename)
        config.set(\
            'Timeseries', 'strftime', self.tformat_editor.text())
        with open(filename, 'wb') as ini_file:
            config.write(ini_file)
        self.accept()
