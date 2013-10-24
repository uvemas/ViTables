#!/usr/bin/env python3
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

"""Plugin that provides columnar organizations for arrays

The plugin let the users to mark several array views (all of them with the
same number of rows) and then display those arrays using a unique widget, one
array next to other. One can think that a set of arrays are displayed as a
table. This seems quite strange to me but is a feature request so I assume
that the plugin will be useful to some users.

Once the plugin is enabled it works on any opened file.
"""

__docformat__ = 'restructuredtext'
__version__ = '1.0'
plugin_class = 'ArrayColsOrganizer'
plugin_name = 'Columnar organization of arrays'
comment = """Rearrange several arrays with the same number of rows and """\
"""displays them in a unique widget"""

import os.path

import tables

from PyQt4 import QtGui
from PyQt4 import QtCore

import vitables
from vitables.vtsite import PLUGINSDIR
from vitables.plugins.columnorg.aboutpage import AboutPage

translate = QtGui.QApplication.translate

LOGGER = vitables.plugin_utils.getLogger()

class ArrayColsOrganizer(QtCore.QObject):
    
    def __init__(self, parent=None):
        """Class constructor.

        Dynamically finds new instances of
        :meth:`vitables.vttables.leaf_model.LeafModel` and customizes them if
        they are arrays that can be grouped in a unique view.
        """

        super(ArrayColsOrganizer, self).__init__(parent)
        self.vtapp = vitables.utils.getVTApp()
        self.vtgui = vitables.plugin_utils.getVTGui()

        # Add an entry under the Node menu
        self.addEntry()

        # Connect signals to slots
        self.vtgui.node_menu.aboutToShow.connect(self.updateNodeMenu)
        self.vtgui.leaf_node_cm.aboutToShow.connect(self.updateNodeMenu)

        # Convenience signal defined in the vtapp module
        self.vtapp.leaf_model_created.connect(self.customizeView)


    def addEntry(self):
        """Add the `Join Arrays`. entry to `Node` menu.
        """

        object_group_icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'columnorg/icons/object-group.png'))
        object_group_icon.addPixmap(pixmap,
                                    QtGui.QIcon.Normal,
                                    QtGui.QIcon.On)

        self.group_action = QtGui.QAction(
            translate('ArrayColsOrganizer',
                "&Group Arrays",
                "Group separated arrays with the same number of rows"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.groupArrays,
            icon=object_group_icon,
            statusTip=translate('ArrayColsOrganizer',
                """Use a unique widget to display Arrays as if they where """
                """columns of a Table""",
                "Status bar text for the Node -> Group Arrays action"))

        # Add the action to the Node menu
        vitables.plugin_utils.addToMenu(self.vtgui.node_menu,
                                        self.group_action)

        # Add the action to the leaf context menu
        vitables.plugin_utils.addToLeafContextMenu(self.group_action)


    def updateNodeMenu(self):
        """Update the `join_action` QAction when the Node menu is pulled down.
        
        The action is disabled when there are less than two Arrays checked, and
        also when not all checked arrays have the same number of rows.

        This method is a slot. See class ctor for details.
        """

        number_of_rows = []
        self.group_action.setEnabled(False)
        for view in self.vtgui.workspace.subWindowList():
            if hasattr(view, 'joined_arrays'):
                number_of_rows.append(view.joined_arrays)
            elif (view.leaf_view.cornerWidget() and\
            view.leaf_view.cornerWidget().isChecked()):
                number_of_rows.append(view.leaf_model.numrows[()])

        if len(number_of_rows) < 2:
            return
        if number_of_rows.count(number_of_rows[0]) == len(number_of_rows):
            self.group_action.setEnabled(True)


    def customizeView(self,datasheet):
        """Add a checkbox in the bottom right corner of array views.

        This is a slot called every time a new view is created.

        """

        datasheet.cb = QtGui.QCheckBox(datasheet)
        datasheet.cb.setToolTip("Group Arrays into a unique view")
    
        # The tables.Node instance tied to that data structure
        pt_node = datasheet.dbt_leaf.node
        if hasattr(pt_node, 'target'):
            # The selected item is a link and must be dereferenced
            leaf = pt_node()
        else:
            leaf = pt_node
    
        if not isinstance(leaf, tables.Table):
            datasheet.leaf_view.setCornerWidget(datasheet.cb)
        
        datasheet.cb.stateChanged.connect(self.chooseAction)


    def chooseAction(self, state):
        """Choose whether group individual arrays or separate grouped arrays.
        
        State = 0 implies that the checkbox is unchecked. On an individual
        array it means that it is not electable to be grouped. In a group of
        arrays it means that the group should be separated.

        State = 2 implies that the checkbox is checked. On both an individual
        array and a group of arrays it means that the checked object can be
        grouped to other checked array/group of arrays.
        
        :Parameter state: the state of the sender checkbox 
        """

        if (state == 0):
            self.separateArrays(self.sender())
        elif (state == 2):
            self.arraysToBeGrouped()


    def separateArrays(self, sender):
        """Separate joined Arrays if needed.

        :Parameter sender: the checkbox that emited the signal
        """
        pass        


    def arraysToBeGrouped(self):
        """The list of array views to be grouped at a given moment.
        """

        self.views_to_group = []
        self.number_of_rows = []
        for view in self.vtgui.workspace.subWindowList():
            if hasattr(view, 'joined_arrays'):
                self.views_to_group.append(view)
                self.number_of_rows.append(view.joined_arrays)
            elif (view.leaf_view.cornerWidget() and\
            view.leaf_view.cornerWidget().isChecked()):
                self.views_to_group.append(view)
                self.number_of_rows.append(view.leaf_model.numrows[()])

        if self.number_of_rows.count(self.number_of_rows[0]) != len(self.number_of_rows):
            print("""\nError: join arrays operation cancelled. Not all the """
                  """selected arrays have the same number of rows.""")


    def groupArrays(self):
        """Group an Array with other Array or with an existing group of Arrays.
        """

        numrows = self.number_of_rows[0]
        # Set the internal widget for the SubWindow that will be created later
        container = QtGui.QWidget()
        hlayout = QtGui.QHBoxLayout()
            
        # Add datasheets to the layout and give this layout to the widget.
        # Datasheets must no have title bar. If they have then the user can
        # move them freely inside the wrapping subwindow
        for datasheet in self.views_to_group:
            title = QtGui.QLabel(datasheet.windowTitle())
            datasheet.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            vertical_layout = QtGui.QVBoxLayout()
            vertical_layout.addWidget(title)
            vertical_layout.addWidget(datasheet)
            hlayout.addLayout(vertical_layout)
        container.setLayout(hlayout)

        # Create the subwindow
        sw = self.vtgui.workspace.addSubWindow(container)
        sw.joined_arrays = numrows
        sw.show()
        self.customizeGroupedViews(sw)


    def customizeGroupedViews(self, sw):
        """Make the joined view widget usable.
        
        - All but the leftmost horizontal header views are hidden
        - All but the rightmost verticals scrollbars are hidden
          and connected beween them
        
        Beware that horizontal scrollbars cannot be connected easily if the
        number of columns differ for the grouped arrays so we recommend to
        group only arrays with the same number of columns.

        :Parameter sw: the viw (QMdiSubWindow instance) being customized
        """
        
        # The top level layout, a horizontal box layout
        sw_layout = sw.widget().layout()
        # The number of children vertical layouts
        vl_count = sw_layout.count()
        # The internal widgets contained by the children layouts are labels
        # and datasheets:
        # horizontal layout -> vertical layout -> widget item -> label
        #                                     |-> widget item -> datasheet 
        datasheets = []
        for i in range(vl_count):
            datasheets.append(sw_layout.itemAt(i).itemAt(1).widget())
        for i in range(vl_count-1):
            datasheets[vl_count-1].widget().verticalScrollBar().valueChanged.connect(
                datasheets[i].widget().verticalScrollBar().setValue)
            datasheets[i+1].widget().verticalHeader().hide()
            datasheets[i].widget().verticalScrollBar().hide()
            datasheets[i].widget().setCornerWidget(None)
        
#     def closeEvent(self, event):
#         # Propagate the event. In the process, self.widget().closeEvent
#         # will be called
#         QtGui.QMdiSubWindow.closeEvent(self, event)
# 
#         if self.vtgui.workspace.subWindowList() == []:
#             self.vtgui.dbs_tree_view.setFocus(True)


    def helpAbout(self, parent):
        """Full description of the plugin.

        This is a convenience method which works as expected by
        :meth:preferences.preferences.Preferences.aboutPluginPage i.e.
        build a page which contains the full description of the plugin
        and, optionally, allows for its configuration.

        :Parameter about_page: the container widget for the page
        """

        # Plugin full description
        desc = {'version': __version__,
            'module_name': os.path.join(os.path.basename(__file__)),
            'folder': os.path.join(os.path.dirname(__file__)),
            'author': 'Vicent Mas <vmas@vitables.org>',
            'about_text': translate('ArraysColsOrganizer',
            """<qt>
            <p>Plugin that provides an alternative view for arrays with
            the same number of rows.
            <p>The user selects the arrays which he want to see in a unique
            viewer. Then clicks on the Node -> Linked View menu entry and
            the arrays are displayed as expected by the user. 
            </qt>""",
            'Text of an About plugin message box')}
        about_page = AboutPage(desc, parent)
        return about_page

