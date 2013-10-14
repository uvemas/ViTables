#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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
This module provides a widget with the full description of the plugin.

The module allows for configuring the plugin too.

The widget is displayed when the plugin is selected in the Preferences
dialog selector tree.
"""

__docformat__ = 'restructuredtext'

import os.path

from PyQt4 import QtGui
from PyQt4.uic import loadUiType

import vitables.utils
from vitables.vtsite import PLUGINSDIR

translate = QtGui.QApplication.translate

# This method of the PyQt4.uic module allows for dinamically loading user 
# interfaces created by QtDesigner. See the PyQt4 Reference Guide for more
# info.
Ui_AboutPage = \
    loadUiType(os.path.join(PLUGINSDIR, 'about_page.ui'))[0]


class AboutPage(QtGui.QWidget, Ui_AboutPage):
    """
    Configure the About page for the csv plugin in the Preferences dialog.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This widget is inserted as a page in the stacked widget of the
    Preferences dialog when the CVS import/export item is clicked in the
    selector tree.

    """

    def __init__(self, desc, parent=None):
        """Fill the widget describing the CSV plugin.

        :Parameter desc: a dictionary with the plugin description
        """

        # Makes the dialog and gives it a layout
        super(AboutPage, self).__init__(parent)
        self.setupUi(self)

        self.version_le.setText(desc['version'])
        self.module_name_le.setText(desc['module_name'])
        self.folder_le.setText(desc['folder'])
        self.author_le.setText(desc['author'])
        self.desc_te.setText(desc['about_text'])
