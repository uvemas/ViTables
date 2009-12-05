# -*- coding: utf-8 -*-
#!/usr/bin/env python

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
Here is defined the NodePropDlg class.

Classes:

* NodePropDlg(QDialog)

Methods:

* __init__(self, info)
* makeGeneralPage(self, info)
* groupGB(self, info, page, title)
* leafGB(self, info, page, table=False)
* makeSysAttrsPage(self, info)
* makeUserAttrsPage(self, info)
* slotDisplayCellContent(self, index)
* slotAddAttr(self)
* slotDelAttr(self)
* accept(self)

Functions:

* trs(source, comment=None)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'NodePropDlg'

import tables

from PyQt4 import QtGui, QtCore

import vitables.utils
from vitables.nodeProperties import nodePropUI
import vitables.nodeProperties.attrEditor as attrEditor



def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))
class NodePropDlg(QtGui.QDialog, nodePropUI.Ui_NodePropDialog):
    """
    Node properties dialog.

    This class displays a tabbed dialog that shows some properties of the
    selected node. First tab, General, shows general properties like name,
    path, type etc. The second and third tabs show the system and user
    attributes in a tabular way.
    """

    def __init__(self, info):
        """:Parameters:

        - `info`: a NodeInfo instance describing a given node
        """

        QtGui.QDialog.__init__(self, QtGui.qApp.activeWindow())
        self.setupUi(self)

        # The dialog caption
        caption_for_type = {
            u'root group': trs('Database properties', 'Dialog caption'), 
            u'group': trs('Group properties', 'Dialog caption'),
            u'table': trs('Table properties', 'Dialog caption'), 
            u'vlarray': trs('VLArray properties', 'Dialog caption'), 
            u'earray': trs('EArray properties', 'Dialog caption'), 
            u'carray': trs('CArray properties', 'Dialog caption'), 
            u'array': trs('Array properties', 'Dialog caption'), }
        self.setWindowTitle(caption_for_type[info.node_type])

        # Customise the dialog's pages
        self.makeGeneralPage(info)
        self.makeSysAttrsPage(info)
        self.makeUserAttrsPage(info)

        # Variables used for checking the table of user attributes
        self.mode = info.mode
        self.asi = info.asi

        self.connect(self.buttons_box, QtCore.SIGNAL('accepted()'), 
                    self.accept)
        self.connect(self.buttons_box, QtCore.SIGNAL('rejected()'), 
                    QtCore.SLOT('reject()'))

        # Show the dialog
        self.show()


    def makeGeneralPage(self, info):
        """Make the General page of the Properties dialog.

        The page contains two groupboxes that are laid out vertically.
        """

        ###############################
        # Setup the Database groupbox #
        ###############################
        if info.node_type == u'root group':
            self.name_ledit.setText(info.filename)
            self.path_ledit.setText(info.filepath)
            self.path_ledit.setToolTip(info.filepath)
            self.type_ledit.setText(info.file_type)
            mode_label = QtGui.QLabel(trs('Access mode:', 'A label'), 
                                    self.database_gb)
            mode_ledit = vitables.utils.customLineEdit(self.database_gb)
            mode_ledit.setText(info.mode)
            self.database_layout.addWidget(mode_label, 3, 0)
            self.database_layout.addWidget(mode_ledit, 3, 1)
        else:
            self.name_ledit.setText(info.nodename)
            self.path_ledit.setText(info.nodepath)
            self.path_ledit.setToolTip(info.nodepath)
            self.type_ledit.setText(info.node_type)

        ############################################
        # Setup the Root group/Group/Leaf groupbox #
        ############################################
        if info.node_type == u'root group':
            title = trs('Root group', 'Title of a groupbox')
            self.groupGB(info, title)
        elif info.node_type == u'group':
            title = trs('Group', 'Title of a groupbox')
            self.groupGB(info, title)
        elif info.node_type.count(u'array'):
            self.leafGB(info, table=False)
        else:
            self.leafGB(info, table=True)


    def groupGB(self, info, title):
        """Make the groupbox of the General page for File/Group instances."""

        #######################################
        # Setup the Group/Root group groupbox #
        #######################################
        self.bottom_gb.setTitle(title)

        # Number of children label
        label = QtGui.QLabel(trs('Number of children:', 'A label'), 
                            self.bottom_gb)
        ledit = vitables.utils.customLineEdit(self.bottom_gb)
        ledit.setText(unicode(len(info.hanging_nodes)))
        self.bottomgb_layout.addWidget(label, 0, 0)
        self.bottomgb_layout.addWidget(ledit, 0, 1)

        # The group's children table
        table = QtGui.QTableView(self.bottom_gb)
        table.verticalHeader().hide()
        table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        background = table.palette().brush(QtGui.QPalette.Window).color()
        table.setStyleSheet("background-color: %s" % background.name())
        self.children_model = QtGui.QStandardItemModel()
        self.children_model.setHorizontalHeaderLabels([
            trs('Child name', 
            'First column header of the table'), 
            trs('Type', 
            'Second column header of the table')])
        table.setModel(self.children_model)
        for name in info.hanging_groups.keys():
            name_item = QtGui.QStandardItem(name)
            name_item.setEditable(False)
            type_item = QtGui.QStandardItem(trs('group'))
            type_item.setEditable(False)
            self.children_model.appendRow([name_item, type_item])
        for name in info.hanging_leaves.keys():
            name_item = QtGui.QStandardItem(name)
            name_item.setEditable(False)
            type_item = QtGui.QStandardItem(trs('leaf'))
            type_item.setEditable(False)
            self.children_model.appendRow([name_item, type_item])
        self.bottomgb_layout.addWidget(table, 1, 0, 1, 2)


    def leafGB(self, info, table=False):
        """Make the groupbox of the General page for Leaf nodes."""

        ################################
        # Setup the Dataspace groupbox #
        ################################
        self.bottom_gb.setTitle(trs('Dataspace', 'Title of a groupbox'))

        # Number of dimensions label
        dim_label = QtGui.QLabel(trs('Dimensions:', 'A label'), self.bottom_gb)
        dim_ledit = vitables.utils.customLineEdit(self.bottom_gb)
        dim_ledit.setText(unicode(len(info.shape)))
        self.bottomgb_layout.addWidget(dim_label, 0, 0)
        self.bottomgb_layout.addWidget(dim_ledit, 0, 1)

        # Shape label
        shape_label = QtGui.QLabel(trs('Shape:', 'A label'), self.bottom_gb)
        shape_ledit = vitables.utils.customLineEdit(self.bottom_gb)
        shape_ledit.setText(unicode(info.shape))
        self.bottomgb_layout.addWidget(shape_label, 1, 0)
        self.bottomgb_layout.addWidget(shape_ledit, 1, 1)

        # Data type label
        dtype_label = QtGui.QLabel(trs('Data type:', 'A label'), 
            self.bottom_gb)
        dtype_ledit = vitables.utils.customLineEdit(self.bottom_gb)
        dtype_ledit.setText(info.dtype)
        self.bottomgb_layout.addWidget(dtype_label, 2, 0)
        self.bottomgb_layout.addWidget(dtype_ledit, 2, 1)

        # Compression library label
        compression_label = QtGui.QLabel(trs('Compression:', 'A label'), 
            self.bottom_gb)
        compression_ledit = vitables.utils.customLineEdit(self.bottom_gb)
        if info.filters.complib is None:
            compression_ledit.setText(unicode('uncompressed', 'utf_8'))
        else:
            compression_ledit.setText(unicode(info.filters.complib, 'utf_8'))
        self.bottomgb_layout.addWidget(compression_label, 3, 0)
        self.bottomgb_layout.addWidget(compression_ledit, 3, 1)

        # Information about the fields of Table instances
        if table:
            # The Table's fields description
            table = QtGui.QTableView(self.bottom_gb)
            table.verticalHeader().hide()
            table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
            background = table.palette().brush(QtGui.QPalette.Window).color()
            table.setStyleSheet("background-color: %s" % background.name())
            self.fields_model = QtGui.QStandardItemModel()
            self.fields_model.setHorizontalHeaderLabels([
                trs('Field name', 
                'First column header of the table'), 
                trs('Type', 
                'Second column header of the table'), 
                trs('Shape', 
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
                    pathname_item.setEditable(False)
                    type_item = QtGui.QStandardItem(trs('nested'))
                    type_item.setEditable(False)
                    shape_item = QtGui.QStandardItem(trs('-'))
                    shape_item.setEditable(False)
                else:
                    pathname_item = QtGui.QStandardItem(unicode(pathname, 
                                                                'utf_8'))
                    pathname_item.setEditable(False)
                    type_item = QtGui.QStandardItem(\
                            unicode(info.columns_types[pathname], 'utf_8'))
                    type_item.setEditable(False)
                    shape_item = QtGui.QStandardItem(\
                                        unicode(info.columns_shapes[pathname]))
                    shape_item.setEditable(False)
                self.fields_model.appendRow([pathname_item, type_item, 
                                            shape_item])
            self.bottomgb_layout.addWidget(table, 4, 0, 1, 2)


    def makeSysAttrsPage(self, info):
        """Make the System attributes page of the Properties dialog."""

        # Number of attributes label
        self.sattr_ledit.setText(\
            vitables.utils.toUnicode(len(info.system_attrs)))

        # Table of system attributes
        self.sys_table.verticalHeader().hide()
        self.sys_table.horizontalHeader().setResizeMode(\
            QtGui.QHeaderView.Stretch)
        self.sysattr_model = QtGui.QStandardItemModel()
        self.sysattr_model.setHorizontalHeaderLabels([
            trs('Name', 
            'First column header of the table'), 
            trs('Value', 
            'Second column header of the table'), 
            trs('Datatype', 
            'Third column header of the table')])
        self.sys_table.setModel(self.sysattr_model)

        # Fill the table
        bg_brush = self.sys_table.palette().brush(QtGui.QPalette.Window)
        base_brush = self.sys_table.palette().brush(QtGui.QPalette.Base)
        for name, value in info.system_attrs.items():
            name = vitables.utils.toUnicode(name)
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
            # Beware that objects whose shape is () are not warrantied
            # to be Python objects, for instance
            # x = numpy.array(3) ->
            # x.shape returns ()
            # type(x) returns numpy.ndarray
            # isinstance(x, int) returns False 
            if isinstance(value, tables.Filters):
                dtype_name = u'tables.filters.Filters'
            elif hasattr(value, u'shape'):
                dtype_name = vitables.utils.toUnicode(value.dtype.name)
                if dtype_name.startswith(u'string'):
                    dtype_name = u'string'
                if dtype_name.startswith(u'unicode'):
                    dtype_name = u'unicode'
            else:
                # Attributes can be scalar Python objects (PyTables <1.1)
                # or non scalar Python objects, e.g. sequences
                dtype_name = vitables.utils.toUnicode(type(value))
            dtype_item = QtGui.QStandardItem(dtype_name)
            dtype_item.setEditable(False)
            dtype_item.setBackground(bg_brush)
            value_item = QtGui.QStandardItem(vitables.utils.toUnicode(value))
            value_item.setEditable(False)
            value_item.setBackground(bg_brush)
            # When the database is in read-only mode the TITLE attribute
            # cannot be edited
            if (name == u'TITLE') and (info.mode != u'read-only'):
                # The position of the TITLE value in the table
                self.title_row = self.sysattr_model.rowCount()
                self.title_before = vitables.utils.toUnicode(value_item.text())
                value_item.setEditable(True)
                value_item.setBackground(base_brush)
            self.sysattr_model.appendRow([name_item, value_item, dtype_item])

        # The cell contents displayer
        self.connect(self.sys_table, QtCore.SIGNAL('clicked(QModelIndex)'), 
                                self.slotDisplayCellContent)


    def makeUserAttrsPage(self, info):
        """Make the User attributes page of the Properties dialog."""

        self.user_attrs_before = []

        # Number of attributes label
        self.uattr_ledit.setText(\
            vitables.utils.toUnicode(len(info.user_attrs)))

        # Table of user attributes
        self.user_table.verticalHeader().hide()
        self.user_table.horizontalHeader().\
                        setResizeMode(QtGui.QHeaderView.Stretch)
        self.userattr_model = QtGui.QStandardItemModel()
        self.userattr_model.setHorizontalHeaderLabels([
            trs('Name', 
            'First column header of the table'), 
            trs('Value', 
            'Second column header of the table'), 
            trs('Datatype', 
            'Third column header of the table')])
        self.user_table.setModel(self.userattr_model)

        # Fill the table
        # The Data Type cell is a combobox with static content
        datatypes = QtCore.QString("""int8 int16 int32 int64 uint8 uint16 """
            """uint32 uint64 float32 float64 complex64 complex128 bool """
            """string unicode python""")
        dtypes_list = QtCore.QStringList(datatypes.split(u' '))

        bg_brush = self.user_table.palette().brush(QtGui.QPalette.Window)
        base_brush = self.user_table.palette().brush(QtGui.QPalette.Base)
        for name, value in info.user_attrs.items():
            name_item = QtGui.QStandardItem(vitables.utils.toUnicode(name))
            dtype_item = QtGui.QStandardItem()
            dtypes_combo = QtGui.QComboBox()
            dtypes_combo.addItems(dtypes_list)
            dtypes_combo.setEditable(False)
            # In PyTables >=1.1 scalar attributes are stored as numarray arrays
            # In PyTables >= 2.0 scalar attributes are stored as numpy arrays
            if hasattr(value, u'shape'):
                dtype_name = vitables.utils.toUnicode(value.dtype.name)
                if dtype_name.startswith(u'string'):
                    dtype_name = u'string'
                if dtype_name.startswith(u'unicode'):
                    dtype_name = u'unicode'
            else:
                # Attributes can be scalar Python objects (PyTables <1.1)
                # or non scalar Python objects, e.g. sequences
                dtype_name = u'python'
            value_item = QtGui.QStandardItem(vitables.utils.toUnicode(value))
            self.userattr_model.appendRow([name_item, value_item, dtype_item])
            dtypes_combo.setCurrentIndex(dtypes_combo.findText(dtype_name))
            self.user_table.setIndexWidget(dtype_item.index(), dtypes_combo)

            # Complex attributes and ND_array attributes need some visual
            # adjustments
            if dtype_name.startswith(u'complex'):
                # Remove parenthesis from the str representation of
                # complex numbers.
                if (vitables.utils.toUnicode(value)[0], \
                    vitables.utils.toUnicode(value)[-1]) == (u'(', u')'):
                    value_item.setText(vitables.utils.toUnicode(value)[1:-1])
            # ViTables doesn't support editing ND-array attributes so
            # they are displayed in non editable cells
            if (hasattr(value, u'shape') and value.shape != ())or\
            (info.mode == u'read-only'):
                editable = False
                brush = bg_brush
            else:
                editable = True
                brush = base_brush
            name_item.setEditable(editable)
            name_item.setBackground(brush)
            value_item.setEditable(editable)
            value_item.setBackground(brush)
            self.user_attrs_before.append((unicode(name_item.text()), 
                unicode(value_item.text()), 
                unicode(dtypes_combo.currentText())))
        self.user_attrs_before.sort()

        # The group of buttons Add, Delete, What's This
        self.page_buttons = QtGui.QButtonGroup(self.userattrs_page)
        self.page_buttons.addButton(self.add_button, 0)
        self.page_buttons.addButton(self.del_button, 1)
        self.page_buttons.addButton(self.help_button, 2)

        # If the database is in read-only mode user attributes cannot be edited
        if info.mode == u'read-only':
            for uid in (0, 1):
                self.page_buttons.button(uid).setEnabled(False)

        self.connect(self.user_table, QtCore.SIGNAL('clicked(QModelIndex)'), 
                                self.slotDisplayCellContent)
        self.connect(self.help_button, QtCore.SIGNAL('clicked()'), 
                                QtGui.QWhatsThis.enterWhatsThisMode)
        self.connect(self.add_button, QtCore.SIGNAL('clicked()'), 
                                self.slotAddAttr)
        self.connect(self.del_button, QtCore.SIGNAL('clicked()'), 
                                self.slotDelAttr)


    def slotDisplayCellContent(self, index):
        """Show the content of the clicked cell in the line edit at bottom.

        This SLOT is connected to clicked SIGNALs coming from both the
        system attributes table and the user attributes table.

        :Parameter index: the model index of the clicked cell
        """

        page = self.tabw.currentIndex()
        if page == 1:
            model_item = self.sysattr_model.itemFromIndex(index)
            self.scc_display.clear()
            self.scc_display.setText(model_item.text())
        elif page == 2:
            model_item = self.userattr_model.itemFromIndex(index)
            self.ucc_display.clear()
            self.ucc_display.setText(model_item.text())

    # SLOT methods for user attributes

    def slotAddAttr(self):
        """Adds a new row to the attributes table.

        This slot is connected to the clicked signal of the ``Add`` button.
        """

        name_item = QtGui.QStandardItem()
        value_item = QtGui.QStandardItem()
        dtype_item = QtGui.QStandardItem()
        self.userattr_model.appendRow([name_item, value_item, dtype_item])

        # The Data Type cell is a combobox with static content
        datatypes = QtCore.QString("""int8 int16 int32 int64 uint8 uint16 """
            """uint32 uint64 float32 float64 complex64 complex128 bool """
            """string unicode python""")
        dtypes_list = QtCore.QStringList(datatypes.split(u' '))
        dtypes_combo = QtGui.QComboBox()
        dtypes_combo.addItems(dtypes_list)
        dtypes_combo.setEditable(False)
        self.user_table.setIndexWidget(dtype_item.index(), dtypes_combo)

        # Start editing the proper cell. If not, clicking Add+Delete
        # would result in the deletion of an attribute different to that
        # just added. It is also more handy as it allows to start editing
        # without double clicking the cell.
        self.user_table.edit(name_item.index())


    def slotDelAttr(self):
        """
        Deletes a user attribute.

        This slot is connected to the clicked signal of the Delete button.
        An attribute is marked for deletion by giving focus to any cell
        of the row describing it (i.e. clicking a cell or selecting its
        contents.
        """

        # If there is not a selected attribute then return
        current_index = self.user_table.currentIndex()
        if not current_index.isValid():
            print trs('Please, select the attribute to be deleted.',
                'A usage text')
            return

        # Get the name of the attribute being deleted
        current_row = current_index.row()
        current_column = current_index.column()
        if current_column != 0:
            current_index = current_index.sibling(current_row, 0)
        name = self.userattr_model.itemFromIndex(current_index).text()

        # Delete the marked attribute
        title = trs('User attribute deletion',
            'Caption of the attr deletion dialog')
        text = trs("""\n\nYou are about to delete the attribute:\n%s\n\n""",
            'Ask for confirmation') % unicode(name)
        itext = ''
        dtext = ''
        buttons = {\
            'Delete': \
                (trs('Delete', 'Button text'), QtGui.QMessageBox.YesRole), 
            'Cancel': \
                (trs('Cancel', 'Button text'), QtGui.QMessageBox.NoRole), 
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
        if hasattr(self, u'title_row'):
            self.title_after = unicode(\
                self.sysattr_model.item(self.title_row, 1).text())
            if self.title_before != self.title_after:
                return True

        # Check user attributes
        self.user_attrs_after = []
        for index in range(0, self.user_table.model().rowCount()):
            name_after = unicode(self.userattr_model.item(index, 0).text())
            value_after = unicode(self.userattr_model.item(index, 1).text())
            dtype_item = self.userattr_model.item(index, 2)
            dtype_combo = self.user_table.indexWidget(dtype_item.index())
            dtype_after = unicode(dtype_combo.currentText())
            self.user_attrs_after.append((name_after, value_after, 
                dtype_after))
        self.user_attrs_after.sort()
        if self.user_attrs_before != self.user_attrs_after:
            return True

        return False


    def accept(self):
        """
        Customised slot for accepted dialogs.

        This is an overwritten method.
        This SLOT is always the last called method whenever the
        apply/ok buttons are pressed.
        """

        # If the file is in read-only mode or the Attribute Set Instance
        # remains unchanged no attribute needs to be updated
        if (self.mode == u'read-only') or (not self.asiChanged()):
            QtGui.QDialog.accept(self)
            return  # This is mandatory!

        # Check the editable attributes
        aeditor = attrEditor.AttrEditor(self.asi, self.title_after, 
            self.user_table)
        attrs_are_ok, error = aeditor.checkAttributes()
        # If the attributes pass correctness checks then update the
        # attributes and close the dialog
        if attrs_are_ok == True:
            aeditor.setAttributes()
            del aeditor
            QtGui.QDialog.accept(self)
            return
        # If not then keep the dialog opened
        else:
            del aeditor
            self.tabw.setCurrentIndex(2)
            self.ucc_display.clear()
            self.ucc_display.setText(error)
