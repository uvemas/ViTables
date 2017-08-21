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
This module displays in a dialog the node information collected by the
:mod:`vitables.nodeprops.nodeinfo` module.

Users' attributes can be edited if the database has been opened in read-write
mode. Otherwise all shown information is read-only.
"""

import logging
import os.path
from vitables.nodeprops import attreditor
import vitables.utils

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy.uic import loadUiType
import tables


__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
# This method of the PyQt5.uic module allows for dynamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_AttrPropDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__), 'attr_prop_dlg.ui'))[0]


log = logging.getLogger(__name__)


class AttrPropDlg(QtWidgets.QDialog, Ui_AttrPropDialog):
    """
    Node properties dialog.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    This class displays a tabbed dialog that shows some properties of
    the selected node. First tab, General, shows general properties like
    name, path, type etc. The second and third tabs show the system and
    user attributes in a tabular way.

    Beware that data types shown in the General page are `PyTables` data
    types so we can deal with `bytes`, `enum`, `time64` and `pseudoatoms`
    (not all of them are supported by ``numpy``).
    However data types shown in the System and User attributes pages are
    ``numpy`` data types because `PyTables` attributes are stored as ``numpy``
    arrays.

    :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
      describing a given node
    """

    def __init__(self, info):
        """Setup the Properties dialog."""

        vtapp = vitables.utils.getVTApp()
        super(AttrPropDlg, self).__init__(vtapp.gui)
        self.setupUi(self)

        # Customise the dialog's pages
        self.fillSysAttrsPage(info)
        self.fillUserAttrsPage(info)
        self.resize(self.size().width(), self.minimumHeight())

        # Variables used for checking the table of user attributes
        self.mode = info.mode
        self.asi = info.asi

    def fillSysAttrsPage(self, info):
        """Fill the page of system attributes.

        :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
          describing a given node
        """

        # Number of attributes label
        self.sattrLE.setText(str(len(info.system_attrs)))

        # Table of system attributes
        self.sysTable.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)
        self.sysattr_model = QtGui.QStandardItemModel()
        self.sysattr_model.setHorizontalHeaderLabels([
            translate('AttrPropDlg', 'Name',
                      'First column header of the table'),
            translate('AttrPropDlg', 'Value',
                      'Second column header of the table'),
            translate('AttrPropDlg', 'Datatype',
                      'Third column header of the table')])
        self.sysTable.setModel(self.sysattr_model)

        # Fill the table
        bg_brush = self.sysTable.palette().brush(QtGui.QPalette.Window)
        base_brush = self.sysTable.palette().brush(QtGui.QPalette.Base)
        for name, value in info.system_attrs.items():
            name_item = QtGui.QStandardItem(name)
            name_item.setEditable(False)
            name_item.setBackground(bg_brush)
            # Find out the attribute datatype.
            # Since PyTables1.1 scalar attributes are stored as numarray arrays
            # Since PyTables2.0 scalar attributes are stored as numpy arrays
            # It includes the TITLE attribute
            # For instance, assume the ASI of a given node is asi. Then
            # if I do asi.test = 3 ->
            # type(asi.test) returns numpy.int32
            # isinstance(asi.test, int) returns True
            # asi.test.shape returns ()
            # asi.test2 = "hello" ->
            # type(asi.test2) returns numpy.string_
            # isinstance(asi.test2, str) returns True
            # asi.test2.shape returns ()
            # Beware that objects whose shape is () are not warranted
            # to be Python objects, for instance
            # x = numpy.array(3) ->
            # x.shape returns ()
            # type(x) returns numpy.ndarray
            # isinstance(x, int) returns False
            if isinstance(value, tables.Filters):
                dtype_name = 'tables.filters.Filters'
            elif hasattr(value, 'shape'):
                dtype_name = value.dtype.name
            else:
                # Attributes can be scalar Python objects (PyTables <1.1)
                # or non scalar Python objects, e.g. sequences
                dtype_name = str(type(value))
            dtype_item = QtGui.QStandardItem(dtype_name)
            dtype_item.setEditable(False)
            dtype_item.setBackground(bg_brush)
            value_item = QtGui.QStandardItem(str(value))
            value_item.setEditable(False)
            value_item.setBackground(bg_brush)
            # When the database is in read-only mode the TITLE attribute
            # cannot be edited
            if (name == 'TITLE') and (info.mode != 'read-only'):
                # The position of the TITLE value in the table
                self.title_row = self.sysattr_model.rowCount()
                self.title_before = value_item.text()
                value_item.setEditable(True)
                value_item.setBackground(base_brush)
            self.sysattr_model.appendRow([name_item, value_item, dtype_item])

    def fillUserAttrsPage(self, info):
        """Fill the page of user attributes.

        :Parameter info: a :meth:`vitables.nodeprops.nodeinfo.NodeInfo` instance
          describing a given node
        """

        self.user_attrs_before = []

        # Number of attributes label
        self.uattrLE.setText(str(len(info.user_attrs)))

        # Table of user attributes
        self.userTable.horizontalHeader().\
            setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.userattr_model = QtGui.QStandardItemModel()
        self.userattr_model.setHorizontalHeaderLabels([
            translate('AttrPropDlg', 'Name',
                      'First column header of the table'),
            translate('AttrPropDlg', 'Value',
                      'Second column header of the table'),
            translate('AttrPropDlg', 'Datatype',
                      'Third column header of the table')])
        self.userTable.setModel(self.userattr_model)

        # Fill the table
        # The Data Type cell is a combobox with static content
        dtypes_list = ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
                       'uint32', 'uint64', 'float32', 'float64', 'complex64',
                       'complex128', 'bool', 'bytes', 'string', 'python']

        # Brushes used for read-only and writable cells
        bg_brush = self.userTable.palette().brush(QtGui.QPalette.Window)
        base_brush = self.userTable.palette().brush(QtGui.QPalette.Base)
        for name, value in info.user_attrs.items():
            name_item = QtGui.QStandardItem(name)
            value_item = QtGui.QStandardItem(str(value))
            dtype_item = QtGui.QStandardItem()
            dtypes_combo = QtWidgets.QComboBox()
            dtypes_combo.addItems(dtypes_list)
            dtypes_combo.setEditable(False)
            # In PyTables >=1.1 scalar attributes are stored as numarray arrays
            # In PyTables >= 2.0 scalar attributes are stored as numpy arrays
            if hasattr(value, 'shape'):
                dtype_name = value.dtype.name
                if dtype_name.startswith('bytes'):
                    dtype_name = 'bytes'
                elif dtype_name.startswith('str'):
                    dtype_name = 'string'
            else:
                # Attributes can be scalar Python objects (PyTables <1.1)
                # or non scalar Python objects, e.g. sequences
                dtype_name = 'python'
            self.userattr_model.appendRow([name_item, value_item, dtype_item])
            dtypes_combo.setCurrentIndex(dtypes_combo.findText(dtype_name))
            self.userTable.setIndexWidget(dtype_item.index(), dtypes_combo)

            # Complex attributes and ND_array attributes need some visual
            # adjustments
            if dtype_name.startswith('complex'):
                # Remove parenthesis from the str representation of
                # complex numbers.
                if (str(value)[0], str(value)[-1]) == ('(', ')'):
                    value_item.setText(str(value)[1:-1])
            # ViTables doesn't support editing ND-array attributes so
            # they are displayed in non editable cells
            if (hasattr(value, 'shape') and value.shape != ())or\
                    (info.mode == 'read-only'):
                editable = False
                brush = bg_brush
            else:
                editable = True
                brush = base_brush
            name_item.setEditable(editable)
            name_item.setBackground(brush)
            value_item.setEditable(editable)
            value_item.setBackground(brush)
            self.user_attrs_before.append((name_item.text(), value_item.text(),
                                           dtypes_combo.currentText()))
        self.user_attrs_before = sorted(self.user_attrs_before[:])

        # The group of buttons Add, Delete, What's This
        self.page_buttons = QtWidgets.QButtonGroup(self.userattrs_page)
        self.page_buttons.addButton(self.addButton, 0)
        self.page_buttons.addButton(self.delButton, 1)
        self.page_buttons.addButton(self.helpButton, 2)

        # If the database is in read-only mode user attributes cannot be edited
        if info.mode == 'read-only':
            for uid in (0, 1):
                self.page_buttons.button(uid).setEnabled(False)

        self.helpButton.clicked.connect(
            QtWidgets.QWhatsThis.enterWhatsThisMode)

    @QtCore.Slot("QModelIndex", name="on_sysTable_clicked")
    @QtCore.Slot("QModelIndex", name="on_userTable_clicked")
    def displaySelectedCell(self, index):
        """Show the content of the clicked cell in the line edit at bottom.

        :Parameter index: the model index of the clicked cell
        """

        page = self.tabw.currentIndex()
        if page == 1:
            model_item = self.sysattr_model.itemFromIndex(index)
            self.systemAttrCellLE.clear()
            self.systemAttrCellLE.setText(model_item.text())
        elif page == 2:
            model_item = self.userattr_model.itemFromIndex(index)
            self.userAttrCellLE.clear()
            self.userAttrCellLE.setText(model_item.text())

    @QtCore.Slot(name="on_addButton_clicked")
    def addAttribute(self):
        """Add a new attribute to the user's attributes table."""

        # The Data Type cell is a combobox with static content
        dtypes_list = ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16',
                       'uint32', 'uint64', 'float32', 'float64', 'complex64',
                       'complex128', 'bool', 'bytes', 'string', 'python']

        name_item = QtGui.QStandardItem()
        value_item = QtGui.QStandardItem()
        dtype_item = QtGui.QStandardItem()
        dtypes_combo = QtWidgets.QComboBox()
        dtypes_combo.addItems(dtypes_list)
        dtypes_combo.setEditable(False)
        self.userattr_model.appendRow([name_item, value_item, dtype_item])
        self.userTable.setIndexWidget(dtype_item.index(), dtypes_combo)

        # Start editing the proper cell. If not, clicking Add+Delete
        # would result in the deletion of an attribute different to that
        # just added. It is also more handy as it allows to start editing
        # without double clicking the cell.
        self.userTable.edit(name_item.index())

    @QtCore.Slot(name="on_delButton_clicked")
    def delAttribute(self):
        """
        Remove an attribute from the user's attributes table.

        This slot is connected to the clicked signal of the `Delete` button.
        An attribute is marked for deletion by giving focus to any cell
        of the row describing it (i.e. clicking a cell or selecting its
        contents).
        """

        # If there is not a selected attribute then return
        current_index = self.userTable.currentIndex()
        if not current_index.isValid():
            log.error(
                translate('AttrPropDlg',
                          'Please, select the attribute to be deleted.',
                          'A usage text'))
            return

        # Get the name of the attribute being deleted
        current_row = current_index.row()
        current_column = current_index.column()
        if current_column != 0:
            current_index = current_index.sibling(current_row, 0)
        name = self.userattr_model.itemFromIndex(current_index).text()

        # Delete the marked attribute
        title = translate('AttrPropDlg', 'User attribute deletion',
                          'Caption of the attr deletion dialog')
        text = translate('AttrPropDlg',
                         "\n\nYou are about to delete the attribute:\n{0}\n\n",
                         'Ask for confirmation').format(name)
        itext = ''
        dtext = ''
        buttons = {
            'Delete':
                (translate('AttrPropDlg', 'Delete', 'Button text'),
                 QtWidgets.QMessageBox.YesRole),
            'Cancel':
                (translate('AttrPropDlg', 'Cancel', 'Button text'),
                 QtWidgets.QMessageBox.NoRole),
        }

        # Ask for confirmation
        answer = vitables.utils.questionBox(title, text, itext, dtext, buttons)
        if answer == 'Delete':
            # Updates the user attributes table
            self.userattr_model.removeRow(current_row)

    def asiChanged(self):
        """Find out if the user has edited some attribute.

        In order to decide if attributes have been edited we compare
        the attribute tables contents at dialog creation time and at
        dialog closing time.
        """

        # Get the value of the TITLE attribute. Checking is required
        # because the attribute is mandatory in PyTables but not in
        # generic HDF5 files
        self.title_after = None
        if hasattr(self, 'title_row'):
            self.title_after = \
                self.sysattr_model.item(self.title_row, 1).text()
            if self.title_before != self.title_after:
                return True

        # Check user attributes
        self.user_attrs_after = []
        for index in range(0, self.userTable.model().rowCount()):
            name_after = self.userattr_model.item(index, 0).text()
            value_after = self.userattr_model.item(index, 1).text()
            dtype_item = self.userattr_model.item(index, 2)
            dtype_combo = self.userTable.indexWidget(dtype_item.index())
            dtype_after = dtype_combo.currentText()
            self.user_attrs_after.append((name_after, value_after,
                                          dtype_after))
        if sorted(self.user_attrs_before) != sorted(self.user_attrs_after):
            return True

        return False

    @QtCore.Slot(name="on_buttonsBox_accepted")
    def accept(self):
        """
        Overwritten slot for accepted dialogs.

        This slot is always the last called method whenever the Apply/Ok
        buttons are pressed.
        """

        # If the file is in read-only mode or the Attribute Set Instance
        # remains unchanged no attribute needs to be updated
        if (self.mode == 'read-only') or (not self.asiChanged()):
            QtWidgets.QDialog.accept(self)
            return  # This is mandatory!

        # Check the editable attributes
        aeditor = attreditor.AttrEditor(self.asi, self.title_after,
                                        self.userTable)
        attrs_are_ok, error = aeditor.checkAttributes()
        # If the attributes pass correctness checks then update the
        # attributes and close the dialog
        if attrs_are_ok is True:
            aeditor.setAttributes()
            del aeditor
            QtWidgets.QDialog.accept(self)
            return
        # If not then keep the dialog opened
        else:
            del aeditor
            self.tabw.setCurrentIndex(2)
            self.userAttrCellLE.clear()
            self.userAttrCellLE.setText(error)
