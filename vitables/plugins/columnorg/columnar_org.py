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
        # Convenience signal defined in the vtapp module
        self.vtapp.leaf_model_created.connect(self.customizeView)


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
            (to_be_joined_views, numrows) = self.listArraysToJoin(self.sender())
            sw = self.joinArrays(to_be_joined_views, numrows)
            self.customizeJoinedViews(sw)


    def separateArrays(self, sender):
        """Separate joined Arrays if needed.

        :Parameter sender: the checkbox that emited the signal
        """

        for view in self.vtgui.workspace.subWindowList()[:]:
            if hasattr(view, 'joined_arrays'):
                self.internal_datasheets = []
                for subwindow in view.children():
                    LOGGER.error('++++ {}'.format(subwindow))
        
        
    
    def listArraysToJoin(self, sender):
        """The list of array views to be joined
        
        :Parameter sender: the checkbox sending the signal
        """

        # The signal sender's parent is a LeafView which is the internal
        # widget of a DataSheet instance
        datasheet = sender.parent().parent()
        numrows = datasheet.leaf_model.numrows[()]
        joined_views = []
        for view in self.vtgui.workspace.subWindowList()[:]:
            if hasattr(view, 'joined_arrays'):
                if view.joined_arrays == numrows:
                    joined_views.append(view)
            elif (view.leaf_view.cornerWidget() and\
            view.leaf_view.cornerWidget().isChecked()):
                if numrows == view.leaf_model.numrows[()]:
                    joined_views.append(view)

        return joined_views, numrows


    def joinArrays(self, joined_views, numrows):
        """Join separated Arrays if needed.

        :Parameters:
        
          - joined_views: the list of views to be joined
          - numrows: the views numbeer of rows
        """

        # Create a joined view. If it already exists then it is reused
        container = None
        sw = None
        if len(joined_views) > 1:
            # If a joined view exists then reuse it
            for datasheet in joined_views:
                if hasattr(datasheet, 'joined_arrays'):
                    container = datasheet.widget()
                    container_layout = container.layout()
                    sw = datasheet
                    break

            # If no joined view exists then set variables to proper values
            if not container:
                container = QtGui.QWidget()
                container_layout = QtGui.QHBoxLayout()
                container.setLayout(container_layout)
                
            # Create a joined view
            for datasheet in joined_views:
                if  hasattr(datasheet, 'joined_arrays'):
                    continue
                container_layout.addWidget(datasheet)
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

