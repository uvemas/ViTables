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
        they are arrays that can be linked in a unique view.
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

        join_icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'columnorg/icons/insert-link.png'))
        join_icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)

        self.join_action = QtGui.QAction(
            translate('ArrayColsOrganizer',
                "&Join Arrays",
                "Join separated arrays with the same number of rows"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey, triggered=self.joinArrays,
            icon=join_icon,
            statusTip=translate('ArrayColsOrganizer',
                """Use a unique widget to display Arrays as if they where """
                """columns of a Table""",
                "Status bar text for the Node -> Join Arrays action"))

        # Add the action to the Node menu
        vitables.plugin_utils.addToMenu(self.vtgui.node_menu,
                                        self.join_action)

        # Add the action to the leaf context menu
        vitables.plugin_utils.addToLeafContextMenu(self.join_action)


    def updateNodeMenu(self):
        """Update the `join_action` QAction when the Node menu is pulled down.
        
        The action is disabled when there are less than two Arrays checked and
        when not all checked arrays have the same number of rows.

        This method is a slot. See class ctor for details.
        """

        number_of_rows = []
        self.join_action.setEnabled(False)
        for view in self.vtgui.workspace.subWindowList():
            if hasattr(view, 'joined_arrays'):
                number_of_rows.append(view.joined_arrays)
            elif (view.leaf_view.cornerWidget() and\
            view.leaf_view.cornerWidget().isChecked()):
                number_of_rows.append(view.leaf_model.numrows[()])

        if len(number_of_rows) < 2:
            return
        if number_of_rows.count(number_of_rows[0]) == len(number_of_rows):
            self.join_action.setEnabled(True)


    def customizeView(self,datasheet):
        """Add a checkbox in the bottom right corner of array views.

        This is a slot called everytime a new view is created.

        """

        datasheet.cb = QtGui.QCheckBox(datasheet)
        datasheet.cb.setToolTip("Can be joined to other Array view")
    
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
        """Choose between joining individual arrays or separating joined arrays.
        
        State = 0 means that the checkbox is unchecked
        State = 2 means that the checkbox is checked
        
        :Parameter state: the state of the sender checkbox 
        """

        if (state == 0):
            self.separateArrays(self.sender())
        elif (state == 2):
            (views_to_join, numrows) = self.arraysToJoin()

            #sw = self.joinArrays(views_to_join, numrows)
            #if sw:
            #    self.customizeJoinedViews(sw)


    def separateArrays(self, sender):
        """Separate joined Arrays if needed.

        :Parameter sender: the checkbox that emited the signal
        """

        for view in self.vtgui.workspace.subWindowList()[:]:
            if hasattr(view, 'joined_arrays'):
                self.internal_datasheets = []
                for subwindow in view.children():
                    LOGGER.error('++++ {}'.format(subwindow))
        
        
    
    def arraysToJoin(self):
        """The list of array views to be joined at a given moment.
        
        """

        views_to_join = []
        number_of_rows = []
        for view in self.vtgui.workspace.subWindowList():
            if hasattr(view, 'joined_arrays'):
                views_to_join.append(view)
                number_of_rows.append(view.joined_arrays)
            elif (view.leaf_view.cornerWidget() and\
            view.leaf_view.cornerWidget().isChecked()):
                views_to_join.append(view)
                number_of_rows.append(view.leaf_model.numrows[()])

        if number_of_rows.count(number_of_rows[0]) != len(number_of_rows):
            print("""\nError: join arrays operation cancelled. Not all the """
                  """selected arrays have the same number of rows.""")
        return views_to_join, number_of_rows[0]


    def joinArrays(self, views_to_join, numrows):
        """Join an Array with other Array or with a group of joined Arrays.

        :Parameters:
          - views_to_join: the list of views to be joined
          - numrows: the views numbeer of rows
        """

        # Create a joined view. If it already exists then it is reused
        container = None
        sw = None
        if len(views_to_join) > 1:
            # If a joined view exists then reuse it
            for datasheet in views_to_join:
                if hasattr(datasheet, 'joined_arrays'):
                    container = datasheet.widget()
                    container_layout = container.layout().childLayout()
                    sw = datasheet
                    break

            # If no joined view exists then set variables to proper values
            if not container:
                container = QtGui.QWidget()
                container_layout = QtGui.QHBoxLayout(container)
                hlayout = QtGui.QHBoxLayout()
                hlayout.setObjectName('internal_hlayout')
                container_layout.addLayout(hlayout)
                #container.setLayout(container_layout)
                
            # Create a joined view
            for datasheet in views_to_join:
                if  hasattr(datasheet, 'joined_arrays'):
                    continue
#                container_layout.addWidget(datasheet)
                hlayout.addWidget(datasheet)
            if not sw:
                sw = self.vtgui.workspace.addSubWindow(container)
                sw.joined_arrays = numrows
                sw.show()
        return sw


    def customizeJoinedViews(self, sw):
        """Make the joined view widget usable.
        
        - All but the leftmost horizontal header views are hidden
        - All but the rightmost verticals scrollbars are hidden
        - A unique horizontal scrollbar is added
        
        :Parameter sw: the viw (QMdiSubWindow instance) being customized
        """
        
        sw_layout = sw.widget().layout()
        internal_items = sw_layout.count()
        internal_widgets = []
        for i in range(internal_items):
            internal_widgets.append(sw_layout.itemAt(i).widget().leaf_view)
        for i in range(1, internal_items):
            internal_widgets[i].verticalHeader().hide()
            internal_widgets[i-1].verticalScrollBar().hide()
            internal_widgets[i-1].setCornerWidget(None)
        
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

