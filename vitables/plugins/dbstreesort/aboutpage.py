#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
This module provides a widget with the full description of the plugin.

The module allows for configuring the plugin too.

The widget is displayed when the plugin is selected in the Preferences
dialog selector pane.
"""

import os.path
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.uic import loadUiType

__docformat__ = 'restructuredtext'

# This method of the PyQt5.uic module allows for dynamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_DBsTreeSortPage = \
    loadUiType(os.path.join(os.path.dirname(__file__),
                            'dbs_tree_sort_page.ui'))[0]


class AboutPage(QtWidgets.QWidget, Ui_DBsTreeSortPage):
    """
    Widget for describing and customizing the Sorting of DBs Tree plugin.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This widget is inserted as a page in the stacked widget of the
    Preferences dialog when the sorting of DBs Tree item is clicked in the
    selector tree.

    """

    def __init__(self, desc, parent=None):
        """Fill and customize the widget describing the DBs sorting plugin.

        :Parameters:
          -`desc` a dictionary with the plugin description
          -`parent` the stacked widget where this About page will be added
        """

        # Makes the dialog and gives it a layout
        super(AboutPage, self).__init__(parent)
        self.setupUi(self)

        # The widget with the OK and Cancel buttons
        self.preferences_dlg = parent.parent()
        self.dlg_box_buttons = self.preferences_dlg.buttonsBox

        # The plugin description
        self.version_le.setText(desc['version'])
        self.module_name_le.setText(desc['module_name'])
        self.folder_le.setText(desc['folder'])
        self.author_le.setText(desc['author'])
        self.desc_te.setText(desc['about_text'])

        # The absolute path of the INI file
        self.ini_filename = \
            os.path.join(os.path.dirname(__file__), 'sorting_algorithm.ini')

        # Read initial configuration from the INI file
        self.config = configparser.ConfigParser()
        default_sorting = 'human'
        try:
            self.config.read_file(open(self.ini_filename))
            self.initial_sorting = self.config['DBsTreeSorting']['algorithm']
        except (IOError, configparser.ParsingError):
            self.initial_sorting = default_sorting

        # Fill the combo with values and choose the current sorting algorithm
        self.algorithms_combobox.insertItems(
            0, ['alphabetical', 'human'])
        current_index = self.algorithms_combobox.findText(self.initial_sorting)
        self.algorithms_combobox.setCurrentIndex(current_index)

        # Connect signals to slots
        self.dlg_box_buttons.button(QtWidgets.QDialogButtonBox.Cancel).clicked.\
            connect(self.cancelAlgorithmChange)
        self.dlg_box_buttons.button(QtWidgets.QDialogButtonBox.Ok).clicked.\
            connect(self.saveAlgorithmChange)

    def cancelAlgorithmChange(self):
        """Restore the initial sorting algorithm in the combobox.

        If the user press the Cancel button changes made in the
        combobox are lost.
        """

        self.config['DBsTreeSorting']['algorithm'] = self.initial_sorting
        with open(self.ini_filename, 'w') as ini_file:
            self.config.write(ini_file)
        # self.preferences_dlg.reject()

    def saveAlgorithmChange(self):
        """Save the combobox current algorithm.
        """

        self.config['DBsTreeSorting']['algorithm'] = \
            self.algorithms_combobox.currentText()
        with open(self.ini_filename, 'w') as ini_file:
            self.config.write(ini_file)
        # self.parent().parent().accept()
