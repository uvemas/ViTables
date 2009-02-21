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
Here is defined the NodePropDlg class.

Classes:

* NodePropDlg(QDialog)

Methods:

* __init__(self, info)
* __tr(self, source, comment=None)
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

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import tables

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import vitables.utils
import vitables.nodeProperties.attrEditor as attrEditor

class NodePropDlg(QDialog):
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

        QDialog.__init__(self, qApp.activeWindow())

        # The dialog caption
        caption_for_type = {
            'root group': self.__tr('Database properties', 'Dialog caption'), 
            'group': self.__tr('Group properties', 'Dialog caption'),
            'table': self.__tr('Table properties', 'Dialog caption'), 
            'vlarray': self.__tr('VLArray properties', 'Dialog caption'), 
            'earray': self.__tr('EArray properties', 'Dialog caption'), 
            'carray': self.__tr('CArray properties', 'Dialog caption'), 
            'array': self.__tr('Array properties', 'Dialog caption'), }
        self.setWindowTitle(caption_for_type[info.node_type])

        # The tabbed widget
        self.tabw = QTabWidget(self)
        general_page = self.makeGeneralPage(info)
        sysattrs_page = self.makeSysAttrsPage(info)
        userattrs_page = self.makeUserAttrsPage(info)
        self.tabw.addTab(general_page, self.__tr('&General', 
            'Title of the first dialog tab'))
        self.tabw.addTab(sysattrs_page, self.__tr('&System Attributes',
            'Title of the second dialog tab'))
        self.tabw.addTab(userattrs_page, self.__tr('&User Attributes',
            'Title of the second dialog tab'))

        # Dialog buttons
        self.buttons_box = QDialogButtonBox(QDialogButtonBox.Ok|
                                            QDialogButtonBox.Cancel)

        # Dialog layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabw)
        layout.addWidget(self.buttons_box)

        # Variables used for checking the table of user attributes
        self.mode = info.mode
        self.asi = info.asi

        self.connect(self.buttons_box, SIGNAL('accepted()'), 
                    self.accept)
        self.connect(self.buttons_box, SIGNAL('rejected()'), 
                    SLOT('reject()'))

        # Show the dialog
        self.show()
    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate('NodePropDlg', source, comment))


    def makeGeneralPage(self, info):
        """Make the General page of the Properties dialog."""

        # The page contains two groupboxes that are laid out vertically
        page = QWidget()
        page_layout = QVBoxLayout(page)

        ###############################
        # Setup the Database groupbox #
        ###############################
        database_gb = QGroupBox(page)
        database_layout = QGridLayout(database_gb)
        database_gb.setTitle(self.__tr('Database', 'Title of a groupbox'))

        # Nodename/filename label
        if info.node_type == 'root group':
            name = info.filename
        else:
            name = info.nodename
        name_label = QLabel(self.__tr('Name:', 'A label'), database_gb)
        name_ledit = vitables.utils.customLineEdit(database_gb)
        name_ledit.setText(name)
        database_layout.addWidget(name_label, 0, 0)
        database_layout.addWidget(name_ledit, 0, 1)

        # Nodepath/filepath label
        if info.node_type == 'root group':
            path = info.filepath
        else:
            path = info.nodepath
        path_label = QLabel(self.__tr('Path:', 'A label'), database_gb)
        path_ledit = vitables.utils.customLineEdit(database_gb)
        path_ledit.setText(path)
        path_ledit.setToolTip(path)
        database_layout.addWidget(path_label, 1, 0)
        database_layout.addWidget(path_ledit, 1, 1)

        # Node type or file format
        type_label = QLabel(self.__tr('Type:', 'A label'), database_gb)
        type_ledit = vitables.utils.customLineEdit(database_gb)
        if info.node_type == 'root group':
            type_ledit.setText(info.file_type)
        else:
            type_ledit.setText(info.node_type)
        database_layout.addWidget(type_label, 2, 0)
        database_layout.addWidget(type_ledit, 2, 1)

        # Database access mode
        if info.node_type == 'root group':
            mode_label = QLabel(self.__tr('Access mode:', 'A label'), 
                                    database_gb)
            mode_ledit = vitables.utils.customLineEdit(database_gb)
            mode_ledit.setText(info.mode)
            database_layout.addWidget(mode_label, 3, 0)
            database_layout.addWidget(mode_ledit, 3, 1)

        #############################
        # Setup the bottom groupbox #
        #############################
        if info.node_type == 'root group':
            title = self.__tr('Root group', 'Title of a groupbox')
            bottom_gb = self.groupGB(info, page, title)
        elif info.node_type == 'group':
            title = self.__tr('Group', 'Title of a groupbox')
            bottom_gb = self.groupGB(info, page, title)
        elif info.node_type.count('array'):
            bottom_gb = self.leafGB(info, page, table=False)
        else:
            bottom_gb = self.leafGB(info, page, table=True)

        # Page layout
        page_layout.addWidget(database_gb)
        page_layout.addWidget(bottom_gb)

        return page
    def groupGB(self, info, page, title):
        """Make the groupbox of the General page for File/Group instances."""

        #######################################
        # Setup the Group/Root group groupbox #
        #######################################
        groupbox = QGroupBox(page)
        layout = QGridLayout(groupbox)
        groupbox.setTitle(title)

        # Number of children label
        label = QLabel(self.__tr('Number of children:', 'A label'), 
                            groupbox)
        ledit = vitables.utils.customLineEdit(groupbox)
        ledit.setText(unicode(len(info.hanging_nodes)))
        layout.addWidget(label, 0, 0)
        layout.addWidget(ledit, 0, 1)

        # The group's children table
        table = QTableView(groupbox)
        table.verticalHeader().hide()
        table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        background = table.palette().brush(QPalette.Window).color()
        table.setStyleSheet("background-color: %s" % background.name())
        self.children_model = QStandardItemModel()
        self.children_model.setHorizontalHeaderLabels([
            self.__tr('Child name', 
            'First column header of the table'), 
            self.__tr('Type', 
            'Second column header of the table')])
        table.setModel(self.children_model)
        for name in info.hanging_groups.keys():
            name_item = QStandardItem(name)
            name_item.setEditable(False)
            type_item = QStandardItem(self.__tr('group'))
            type_item.setEditable(False)
            self.children_model.appendRow([name_item, type_item])
        for name in info.hanging_leaves.keys():
            name_item = QStandardItem(name)
            name_item.setEditable(False)
            type_item = QStandardItem(self.__tr('leaf'))
            type_item.setEditable(False)
            self.children_model.appendRow([name_item, type_item])
        layout.addWidget(table, 1, 0, 1, 2)

        return groupbox

    def leafGB(self, info, page, table=False):
        """Make the groupbox of the General page for Leaf nodes."""

        ################################
        # Setup the Dataspace groupbox #
        ################################
        groupbox = QGroupBox(page)
        layout = QGridLayout(groupbox)
        groupbox.setTitle(self.__tr('Dataspace', 'Title of a groupbox'))

        # Number of dimensions label
        dim_label = QLabel(self.__tr('Dimensions:', 'A label'), groupbox)
        dim_ledit = vitables.utils.customLineEdit(groupbox)
        dim_ledit.setText(unicode(len(info.shape)))
        layout.addWidget(dim_label, 0, 0)
        layout.addWidget(dim_ledit, 0, 1)

        # Shape label
        shape_label = QLabel(self.__tr('Shape:', 'A label'), groupbox)
        shape_ledit = vitables.utils.customLineEdit(groupbox)
        shape_ledit.setText(unicode(info.shape))
        layout.addWidget(shape_label, 1, 0)
        layout.addWidget(shape_ledit, 1, 1)

        # Data type label
        dtype_label = QLabel(self.__tr('Data type:', 'A label'), 
            groupbox)
        dtype_ledit = vitables.utils.customLineEdit(groupbox)
        dtype_ledit.setText(info.dtype)
        layout.addWidget(dtype_label, 2, 0)
        layout.addWidget(dtype_ledit, 2, 1)

        # Compression library label
        compression_label = QLabel(self.__tr('Compression:', 'A label'), 
            groupbox)
        compression_ledit = vitables.utils.customLineEdit(groupbox)
        if info.filters.complib is None:
            compression_ledit.setText(unicode('uncompressed', 'utf_8'))
        else:
            compression_ledit.setText(unicode(info.filters.complib, 'utf_8'))
        layout.addWidget(compression_label, 3, 0)
        layout.addWidget(compression_ledit, 3, 1)

        # Information about the fields of Table instances
        if table:
            # The Table's fields description
            table = QTableView(groupbox)
            table.verticalHeader().hide()
            table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
            background = table.palette().brush(QPalette.Window).color()
            table.setStyleSheet("background-color: %s" % background.name())
            self.fields_model = QStandardItemModel()
            self.fields_model.setHorizontalHeaderLabels([
                self.__tr('Field name', 
                'First column header of the table'), 
                self.__tr('Type', 
                'Second column header of the table'), 
                self.__tr('Shape', 
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
                    pathname_item = QStandardItem(field_name)
                    pathname_item.setEditable(False)
                    type_item = QStandardItem(self.__tr('nested'))
                    type_item.setEditable(False)
                    shape_item = QStandardItem(self.__tr('-'))
                    shape_item.setEditable(False)
                else:
                    pathname_item = QStandardItem(unicode(pathname, 
                                                                'utf_8'))
                    pathname_item.setEditable(False)
                    type_item = QStandardItem(\
                            unicode(info.columns_types[pathname], 'utf_8'))
                    type_item.setEditable(False)
                    shape_item = QStandardItem(\
                                        unicode(info.columns_shapes[pathname]))
                    shape_item.setEditable(False)
                self.fields_model.appendRow([pathname_item, type_item, 
                                            shape_item])
            layout.addWidget(table, 4, 0, 1, 2)

        return groupbox

    def makeSysAttrsPage(self, info):
        """Make the System attributes page of the Properties dialog."""

        # The page contains a label and a table that laid out vertically
        page = QWidget()
        page_layout = QGridLayout(page)

        # Number of attributes label
        nattr_label = QLabel(self.__tr('System attributes:', 'A label'), 
                                    page)
        nattr_ledit = vitables.utils.customLineEdit(page)
        nattr_ledit.setText(unicode(len(info.system_attrs)))
        page_layout.addWidget(nattr_label, 0, 0)
        page_layout.addWidget(nattr_ledit, 0, 1)

        # Table of system attributes
        sys_table = QTableView(page)
        sys_table.verticalHeader().hide()
        sys_table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.sysattr_model = QStandardItemModel()
        self.sysattr_model.setHorizontalHeaderLabels([
            self.__tr('Name', 
            'First column header of the table'), 
            self.__tr('Value', 
            'Second column header of the table'), 
            self.__tr('Datatype', 
            'Third column header of the table')])
        sys_table.setModel(self.sysattr_model)

        # Fill the table
        bg_brush = page.palette().brush(QPalette.Background)
        base_brush = page.palette().brush(QPalette.Base)
        for name, value in info.system_attrs.items():
            name_item = QStandardItem(unicode(name, 'utf_8'))
            name_item.setEditable(False)
            name_item.setBackground(bg_brush)
            # Find out the attribute datatype.
            if isinstance(value, tables.Filters):
                dtype_name = unicode('tables.filters.Filters', 'utf_8')
            # Since PyTables1.1 scalar attributes are stored as numarray arrays
            # Since PyTables2.0 scalar attributes are stored as numpy arrays
            # It includes the TITLE attribute
            elif isinstance(value, str):
                dtype_name = unicode('string', 'utf_8')
            elif hasattr(value, 'shape'):
                dtype_name = unicode(value.dtype.name, 'utf_8')
            else:
                # The attributes are scalar Python objects (PyTables<1.1)
                # or N-dimensional attributes
                dtype_name = unicode(type(value), 'utf_8')
            dtype_item = QStandardItem(dtype_name)
            dtype_item.setEditable(False)
            dtype_item.setBackground(bg_brush)
            if dtype_name.startswith('string'):
                value_item = QStandardItem(unicode(value, 'utf_8'))
            else:
                value_item = QStandardItem(unicode(value))
            value_item.setEditable(False)
            value_item.setBackground(bg_brush)
            # When the database is in read-only mode the TITLE attribute
            # cannot be edited
            if (name == 'TITLE') and (info.mode != 'read-only'):
                # The position of the TITLE value in the table
                self.title_row = self.sysattr_model.rowCount()
                value_item.setEditable(True)
                value_item.setBackground(base_brush)
            self.sysattr_model.appendRow([name_item, value_item, dtype_item])
        page_layout.addWidget(sys_table, 1, 0, 1, 2)

        # The cell contents displayer
        self.scc_display = vitables.utils.customLineEdit(page)
        self.scc_display.setFrame(True)
        page_layout.addWidget(self.scc_display, 2, 0, 1, 2)

        self.connect(sys_table, SIGNAL('clicked(QModelIndex)'), 
                                self.slotDisplayCellContent)

        return page
    def makeUserAttrsPage(self, info):
        """Make the User attributes page of the Properties dialog."""

        # The page contains a label, a table and a group of buttons.
        # This components are laid out vertically
        page = QWidget()
        page_layout = QGridLayout(page)

        # Number of attributes label
        nattr_label = QLabel(self.__tr('User attributes:', 'A label'), 
                                    page)
        nattr_ledit = vitables.utils.customLineEdit(page)
        nattr_ledit.setText(unicode(len(info.user_attrs)))
        page_layout.addWidget(nattr_label, 0, 0)
        page_layout.addWidget(nattr_ledit, 0, 1)

        # Table of user attributes
        self.user_table = QTableView(page)
        self.user_table.verticalHeader().hide()
        self.user_table.horizontalHeader().\
                        setResizeMode(QHeaderView.Stretch)
        self.userattr_model = QStandardItemModel()
        self.userattr_model.setHorizontalHeaderLabels([
            self.__tr('Name', 
            'First column header of the table'), 
            self.__tr('Value', 
            'Second column header of the table'), 
            self.__tr('Datatype', 
            'Third column header of the table')])
        self.user_table.setModel(self.userattr_model)

        # Fill the table
        # The Data Type cell is a combobox with static content
        datatypes = QString("""int8 int16 int32 int64 uint8 uint16 """
            """uint32 uint64 float32 float64 complex64 complex128 bool """
            """string python""")
        dtypes_list = QStringList(datatypes.split(' '))

        bg_brush = page.palette().brush(QPalette.Background)
        base_brush = page.palette().brush(QPalette.Base)
        for name, value in info.user_attrs.items():
            name_item = QStandardItem(unicode(name, 'utf_8'))
            dtype_item = QStandardItem()
            dtypes_combo = QComboBox()
            dtypes_combo.addItems(dtypes_list)
            dtypes_combo.setEditable(False)
            # In PyTables < 1.1 scalar attributes are stored as Python objects
            # In PyTables >=1.1 scalar attributes are stored as numarray arrays
            # In PyTables >= 2.0 scalar attributes are stored as numpy arrays
            if hasattr(value, 'shape'):
                dtype_name = unicode(value.dtype.name, 'utf_8').encode('utf_8')
                if dtype_name.startswith('string'):
                    dtype_name = 'string'
            else:
                # But attributes can also be non scalar Python objects.
                dtype_name = 'python'
            if dtype_name.startswith('string'):
                value_item = QStandardItem(unicode(value, 'utf_8'))
            else:
                value_item = QStandardItem(unicode(value))
            self.userattr_model.appendRow([name_item, value_item, dtype_item])
            dtypes_combo.setCurrentIndex(dtypes_combo.findText(dtype_name))
            self.user_table.setIndexWidget(dtype_item.index(), dtypes_combo)

            # Complex attributes and ND_array attributes need some visual
            # adjustments
            if dtype_name.startswith('complex'):
                # Remove parenthesis from the str representation of
                # complex numbers.
                if (unicode(value)[0], unicode(value)[-1]) == ('(', ')'):
                    value_item.setText(unicode(value)[1:-1])
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
        page_layout.addWidget(self.user_table, 1, 0, 1, 2)

        self.user_table.setWhatsThis(self.__tr(
            """<qt>
            <h3>User's attributes editing table</h3>
            Here you can perform the editing of user's attributes for
            this node. It is quite straightforward. <p>For adding an
            attribute click the <b>Add</b> button. A new row will
            be added to the table. Enter the attribute name and its
            value in the corresponding cells. Finally, select the
            attribute datatype in the combobox of the DataType column.
            In order to delete an attribute just select it by clicking
            any of its cells, then click the <b>Delete</b> button.</p>
            <p>Beware that PyTables stores scalar attributes as numpy
            scalar arrays so you will be unable to save them as Python
            objects even if you choose the Python datatype in the
            combobox selector. Also note that multidimensional attributes
             other than Python lists and tuples are not supported.</p>
            </qt>""",
            'Help text for the User Attributes page')
            )

        # The cell contents displayer
        self.ucc_display = vitables.utils.customLineEdit(page)
        self.ucc_display.setFrame(True)
        page_layout.addWidget(self.ucc_display, 2, 0, 1, 2)

        # The group of buttons Add, Delete, What's This
        self.page_buttons = QButtonGroup(page)
        add_button = QPushButton('&Add')
        del_button = QPushButton('&Delete')
        help_button = QPushButton("&What's This")
        self.page_buttons.addButton(add_button, 0)
        self.page_buttons.addButton(del_button, 1)
        self.page_buttons.addButton(help_button, 2)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(del_button)
        buttons_layout.addWidget(help_button)
        buttons_layout.addStretch(1)
        page_layout.addLayout(buttons_layout, 3, 0, 1, 2)

        # If the database is in read-only mode user attributes cannot be edited
        if info.mode == 'read-only':
            for uid in (0, 1):
                self.page_buttons.button(uid).setEnabled(False)

        self.connect(self.user_table, SIGNAL('clicked(QModelIndex)'), 
                                self.slotDisplayCellContent)
        self.connect(help_button, SIGNAL('clicked()'), 
                                QWhatsThis.enterWhatsThisMode)
        self.connect(add_button, SIGNAL('clicked()'), 
                                self.slotAddAttr)
        self.connect(del_button, SIGNAL('clicked()'), 
                                self.slotDelAttr)

        return page
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

        self.user_attr_edited = True

        # Add a new empty row to the User Attributes table
        name_item = QStandardItem()
        value_item = QStandardItem()
        dtype_item = QStandardItem()
        self.userattr_model.appendRow([name_item, value_item, dtype_item])

        # The Data Type cell is a combobox with static content
        datatypes = QString("""int8 int16 int32 int64 uint8 uint16 """
            """uint32 uint64 float32 float64 complex64 complex128 bool """
            """string python""")
        dtypes_list = QStringList(datatypes.split(' '))
        dtypes_combo = QComboBox()
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

        self.user_attr_edited = True

        # If there is not a selected attribute then return
        current_index = self.user_table.currentIndex()
        if not current_index.isValid():
            print self.__tr('Please, select the attribute to be deleted.',
                'A usage text')
            return

        # Get the name of the attribute being deleted
        current_row = current_index.row()
        current_column = current_index.column()
        if current_column != 0:
            current_index = current_index.sibling(current_row, 0)
        name = self.userattr_model.itemFromIndex(current_index).text()

        # Delete the marked attribute
        del_mb = QMessageBox.question(self,
            self.__tr('User attribute deletion',
            'Caption of the attr deletion dialog'),
            self.__tr("""\n\nYou are about to delete the attribute:\n%s\n\n""",
            'Ask for confirmation') % unicode(name, 'utf_8'),
            QMessageBox.Yes|QMessageBox.Default,
            QMessageBox.No|QMessageBox.Escape)

        # OK returns Accept, Cancel returns Reject
        if del_mb == QMessageBox.Yes:
            # Updates the user attributes table
            self.userattr_model.removeRow(current_row)

    def accept(self):
        """
        Customised slot for accepted dialogs.

        This is an overwritten method.
        This SLOT is always the last called method whenever the
        apply/ok buttons are pressed.
        """

        if self.mode == 'read-only':
            QDialog.accept(self)
        else:
            # Get the value of the TITLE attribute. Checking is required
            # because the attribute is mandatory in PyTables but not in
            # generic HDF5 files
            if hasattr(self, 'title_row'):
                title = self.sysattr_model.item(self.title_row, 1).text()
            else:
                title = None
            # Check the editable attributes
            aeditor = attrEditor.AttrEditor(self.asi, title, self.user_table)
            attrs_are_ok, error = aeditor.checkAttributes()
            # If the attributes pass correctness checks then update the
            # attributes and close the dialog
            if attrs_are_ok == True:
                aeditor.setAttributes()
                del aeditor
                QDialog.accept(self)
            # If not then keep the dialog opened
            else:
                del aeditor
                self.tabw.setCurrentIndex(2)
                self.ucc_display.clear()
                self.ucc_display.setText(error)
