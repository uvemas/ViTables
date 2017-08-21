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
A form with tables.Leaf information collected by the
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
Ui_LeafPropPage = \
    loadUiType(os.path.join(os.path.dirname(__file__), 'leaf_prop_page.ui'))[0]


class LeafPropPage(QtWidgets.QWidget, Ui_LeafPropPage):
    """
    Leaf properties page.

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
        super(LeafPropPage, self).__init__(vtapp.gui)
        self.setupUi(self)

        # Customise the dialog's pages
        self.fillGeneralPage(info)

    def fillGeneralPage(self, info):
        """Make the General page of the Properties dialog.

        The page contains two groupboxes that are laid out vertically.

        :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
          describing a given node
        """

        self.nameLE.setText(info.nodename)
        self.pathLE.setText(info.nodepath)
        self.pathLE.setToolTip(info.nodepath)
        self.typeLE.setText(info.node_type)

        self.dimLE.setText(str(len(info.shape)))
        self.shapeLE.setText(str(info.shape))
        self.dtypeLE.setText(info.type)
        if info.filters.complib is None:
            self.compressionLE.setText('uncompressed')
        else:
            self.compressionLE.setText(str(info.filters.complib))

        # Information about the fields of Table instances
        if info.node_type == 'table':
            table = self.recordsTable
            # The Table's fields description
            table.horizontalHeader().setSectionResizeMode(
                QtWidgets.QHeaderView.Stretch)
            # QtGui.QPalette.Window constant is 10
            bg_name = table.palette().brush(10).color().name()
            table.setStyleSheet("background-color: {0}".format(bg_name))
            self.fields_model = QtGui.QStandardItemModel()
            self.fields_model.setHorizontalHeaderLabels(
                [translate('LeafPropPage', 'Field name',
                           'First column header of the table'),
                 translate('LeafPropPage', 'Type',
                           'Second column header of the table'),
                 translate('LeafPropPage', 'Shape',
                           'Third column header of the table')])
            table.setModel(self.fields_model)

            # Fill the table. Nested fields will appear as (colname, nested, -)
            seen_paths = []
            for pathname in info.columns_pathnames:
                if pathname.count('/'):
                    field_name = pathname.split('/')[0]
                    if field_name in seen_paths:
                        continue
                    else:
                        seen_paths.append(field_name)
                    pathname_item = QtGui.QStandardItem(field_name)
                    type_item = QtGui.QStandardItem(
                        translate('LeafPropPage', 'nested'))
                    shape_item = QtGui.QStandardItem(
                        translate('LeafPropPage', '-'))
                else:
                    pathname_item = QtGui.QStandardItem(str(pathname))
                    type_item = QtGui.QStandardItem(
                            str(info.columns_types[pathname]))
                    shape_item = QtGui.QStandardItem(
                                        str(info.columns_shapes[pathname]))
                self.fields_model.appendRow([pathname_item, type_item,
                                            shape_item])

    def arrayPage(self):
        """Remove widgets regarding root groups.
        """

        # Remove the table of fields and datatypes
        self.dataspace_layout.removeWidget(self.recordsTable)
        self.recordsTable.deleteLater()
