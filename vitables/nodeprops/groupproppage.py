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
A form with tables.Group information collected by the
:mod:`vitables.nodeprops.nodeinfo` module.
"""

import os.path

from qtpy import QtGui
from qtpy import QtWidgets

from qtpy.uic import loadUiType

import vitables.utils

__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
# This method of the PyQt5.uic module allows for dinamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_GroupPropPage = \
    loadUiType(os.path.join(os.path.dirname(__file__),'group_prop_page.ui'))[0]



class GroupPropPage(QtWidgets.QWidget, Ui_GroupPropPage):
    """
    Group properties page.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This class displays a tabbed dialog that shows some properties of
    the selected node. First tab, General, shows general properties like
    name, path, type etc. The second and third tabs show the system and
    user attributes in a tabular way.

    Beware that data types shown in the General page are `PyTables` data
    types so we can deal with `enum`, `time64` and `pseudoatoms` (none of them
    are supported by ``numpy``).
    However data types shown in the System and User attributes pages are
    ``numpy`` data types because `PyTables` attributes are stored as ``numpy``
    arrays.

    :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
      describing a given node
    """

    def __init__(self, info):
        """Setup the File Properties page."""

        vtapp = vitables.utils.getVTApp()
        super(GroupPropPage, self).__init__(vtapp.gui)
        self.setupUi(self)

        # Customise the dialog's pages
        self.fillGeneralPage(info)


    def fillGeneralPage(self, info):
        """Make the General page of the Properties dialog.

        The page contains two groupboxes that are laid out vertically.

        :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
          describing a given node
        """

        if info.node_type == 'root group':
            self.nameLE.setText(info.filename)
            self.pathLE.setText(info.filepath)
            self.pathLE.setToolTip(info.filepath)
            self.typeLE.setText(info.file_type)
            self.modeLE.setText(info.mode)
        else:
            self.nameLE.setText(info.nodename)
            self.pathLE.setText(info.nodepath)
            self.pathLE.setToolTip(info.nodepath)
            self.typeLE.setText(info.node_type)

        # Number of children label
        self.nchildrenLE.setText(str(len(info.hanging_nodes)))

        # The group's children table
        table = self.nchildrenTable
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        background = table.palette().brush(QtGui.QPalette.Window).color()
        table.setStyleSheet("background-color: {0}".format(background.name()))
        self.children_model = QtGui.QStandardItemModel()
        self.children_model.setHorizontalHeaderLabels([
            translate('GroupPropPage', 'Child name',
            'First column header of the table'),
            translate('GroupPropPage', 'Type',
            'Second column header of the table')])
        table.setModel(self.children_model)
        for name in info.hanging_groups.keys():
            name_item = QtGui.QStandardItem(name)
            type_item = QtGui.QStandardItem(translate('GroupPropPage',
                'group'))
            self.children_model.appendRow([name_item, type_item])
        for name in info.hanging_leaves.keys():
            name_item = QtGui.QStandardItem(name)
            type_item = QtGui.QStandardItem(translate('GroupPropPage', 'leaf'))
            self.children_model.appendRow([name_item, type_item])
        for name in info.hanging_links.keys():
            name_item = QtGui.QStandardItem(name)
            type_item = QtGui.QStandardItem(translate('GroupPropPage', 'link'))
            self.children_model.appendRow([name_item, type_item])


    def regularGroupPage(self):
        """Remove widgets regarding root groups.
        """

        # Remove the Access mode widgets
        self.dblayout.removeWidget(self.modeLabel)
        self.dblayout.removeWidget(self.modeLE)
        self.modeLabel.deleteLater()
        self.modeLE.deleteLater()

        # Change the title of the group box
        self.bottomGB.setTitle(translate('GroupPropPage', 'Group',
            'Title of the group box'))
