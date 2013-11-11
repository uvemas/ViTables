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
    """The grouped arrays widget.
    """
    
    def __init__(self, parent=None):
        """Class constructor.

        Dynamically finds new instances of
        :meth:`vitables.vttables.leaf_model.LeafModel` and customizes them if
        they are arrays that can be grouped in a unique view.
        """

        super(ArrayColsOrganizer, self).__init__(parent)
        self.vtapp = vitables.utils.getVTApp()
        
        # An specialized object will deal with the Node menu changes
        self.menu_updater = MenuUpdater()
        self.menu_updater.addEntry()

        # Connect convenience signal defined in the vtapp module to slot
        self.vtapp.leaf_model_created.connect(self.customizeView)


    def customizeView(self,datasheet):
        """Add a checkbox in the bottom right corner of array views.

        Customization is twofold: add a checkbox to the LeafView and add a 
        is_checked` attr to the view. In addition, the checkbox has an `array`
        (or `group`) attribute that points to the view (datasheet or group)
        containing it.

        In a regular array, if checkbox ticked, it means that the array is
        candidate to be added to other single/grouped arrays.
        In a group of arrays, if checkbox is ticked it means that the group
        can be group with other ticked single/grouped arrays. If the grouped
        array is the only ticked view then it means that it is a candidate for
        being ungrouped.

        This is a slot called every time a new view is created.

        """

        # The tables.Node instance tied to that data structure
        pt_node = datasheet.dbt_leaf.node
        if hasattr(pt_node, 'target'):
            # The selected item is a link and must be dereferenced
            leaf = pt_node()
        else:
            leaf = pt_node

        if not isinstance(leaf, tables.Table):
            cb = QtGui.QCheckBox(datasheet)
            cb.setToolTip("Group Arrays into a unique view")
            datasheet.leaf_view.setCornerWidget(cb)
            # Attributes for retrieving the state of the checkbox from the
            # datasheet being customized
            cb.source_array = datasheet
            datasheet.is_checked = datasheet.leaf_view.cornerWidget().checkState()

        # Connect signals to slots
        cb.stateChanged.connect(self.cbStateChanged)


    def cbStateChanged(self, state):
        """Update the `is_checked` attribute of DataSheets and GroupedArrays.
        """

        view = self.sender().source_array
        view.is_checked = state


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


class MenuUpdater(QtCore.QObject):

    def __init__(self, parent=None):
        """The constructor method.
        """

        super(MenuUpdater, self).__init__(parent)
        self.vtgui = vitables.plugin_utils.getVTGui()
        
        # Connect signals to slots
        self.vtgui.node_menu.aboutToShow.connect(self.updateNodeMenu)
        self.vtgui.leaf_node_cm.aboutToShow.connect(self.updateNodeMenu)


    def addEntry(self):
        """Add the `Group Arrays` and `Ungroup Arrays` entries to `Node` menu.
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
            statusTip=translate('MenuUpdater',
                """Use a unique widget to display Arrays as if they where """
                """columns of a Table""",
                "Status bar text for the Node -> Group Arrays action"))

        object_ungroup_icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(PLUGINSDIR, \
            'columnorg/icons/object-ungroup.png'))
        object_ungroup_icon.addPixmap(pixmap,
                                    QtGui.QIcon.Normal,
                                    QtGui.QIcon.On)

        self.ungroup_action = QtGui.QAction(
            translate('MenuUpdater',
                "&Ungroup Arrays",
                "Ungroup previously grouped arrays."),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.ungroupArrays,
            icon=object_ungroup_icon,
            statusTip=translate('MenuUpdater',
                """Ungroup previously grouped arrays.""",
                "Status bar text for the Node -> Ungroup Arrays action"))

        # Add the actions to the Node menu
        vitables.plugin_utils.addToMenu(self.vtgui.node_menu,
                                        (self.group_action,
                                        self.ungroup_action))

        # Add the actions to the leaf context menu
        vitables.plugin_utils.addToLeafContextMenu((self.group_action,
                                                   self.ungroup_action))


    def updateNodeMenu(self):
        """Update (un)group_action QActions if the Node menu is about to show.
        
        The `group_action` is disabled when there are less than two Arrays
        checked, and also when not all checked arrays have the same number of
        rows.

        The `ungroup_action` is enabled only if there are one array group
        selected.

        """

        self.group_action.setEnabled(False)
        self.ungroup_action.setEnabled(False)
        checked_views = []
        numrows = []
        for view in self.vtgui.workspace.subWindowList():
            # Both Datasheet and GroupedArray instances have an is_checked attr
            # but Table instances don't have it.
            if hasattr(view, 'is_checked') and (view.is_checked ==
                                                QtCore.Qt.Checked):
                checked_views.append(view)
                if isinstance(view, GroupedArrays):
                    numrows.append(view.grouped_arrays_nrows)
                elif isinstance(view, vitables.vttables.datasheet.DataSheet):
                    numrows.append(view.leaf_model.numrows[()])
 
        self.checked_views = checked_views

        if len(checked_views) == 1:
            if isinstance(checked_views[0], GroupedArrays):
                self.ungroup_action.setEnabled(True)
        elif len(checked_views) > 1:
            if numrows.count(numrows[0]) == len(numrows):
                self.group_action.setEnabled(True)
            else:
                print("""\nError: grouping arrays, operation cancelled. """
                      """Not all the selected arrays have the same number """
                      """of rows.""")


    def groupArrays(self):
        GroupedArrays(arrays=self.checked_views)

    def ungroupArrays(self):
        pass


class GroupedArrays(QtGui.QMdiSubWindow):
    """A widget that contains a group of Arrays.
    """
    
    def __init__(self, parent=None, flags=QtCore.Qt.SubWindow,
                 arrays=None):
        """Make a widget that will display the group of passed arrays
        
        """

        self.vtgui = vitables.plugin_utils.getVTGui()
        super(GroupedArrays, self).__init__(self.vtgui.workspace, flags)

        # The components from which the GraoupedArrays will be made.
        # We use sets instead of lists
        self.arrays = {i for i in arrays}
        self.already_grouped  = set([])
        for i in self.arrays.copy():
            if hasattr(i, 'grouped_arrays_nrows'):
                self.already_grouped.add(i)
                self.arrays.remove(i)
#        LOGGER.error('++++ len(arrays) {}'.format(len(self.arrays)))
#        LOGGER.error('++++ len(already_grouped) {}'.format(len(self.already_grouped)))
        # Create a GroupedArrays object from the set of regular arrays
        self.pindex = QtCore.QModelIndex()
        if (len(self.arrays) > 1):
            self.container = QtGui.QWidget()
            self.getGALayout = self.combineArrays
            ga_layout = self.getGALayout(self.arrays)
            self.container.setLayout(ga_layout)
            self.setWidget(self.container)
            self.grouped_arrays_nrows = \
                ga_layout.itemAt(0).itemAt(1).widget().leaf_model.numrows[()]
            self.already_grouped.add(self)
            # Create the subwindow
            self.show()
#             LOGGER.error('++++ container {}\n     ga_layout {}\n'.format(self.container, ga_layout))
#             LOGGER.error('++++ itemAt0 {}\n     itemAt1 {}\n     itemAt2 {}'.format(ga_layout.itemAt(0),
#                                                                                  ga_layout.itemAt(1),
#                                                                                  ga_layout.itemAt(2)))
#             LOGGER.error('++++ itemAt0.itemAt0 {}\n     itemAt1itemAt0 {}\n     itemAt2itemAt0 {}'.
#                          format(ga_layout.itemAt(0).itemAt(0),
#                                 ga_layout.itemAt(1).itemAt(0),
#                                 ga_layout.itemAt(2).itemAt(0)))
#             LOGGER.error('++++ itemAt0.itemAt0widget {}\n     itemAt1itemAt0widget {}\n     itemAt2itemAt0widget {}'.
#                          format(ga_layout.itemAt(0).itemAt(0).widget(),
#                                 ga_layout.itemAt(1).itemAt(0).widget(),
#                                 ga_layout.itemAt(2).itemAt(0).widget()))
#             LOGGER.error('++++ itemAt0.itemAt1 {}\n     itemAt1itemAt1 {}\n     itemAt2itemAt1 {}'.
#                          format(ga_layout.itemAt(0).itemAt(1),
#                                 ga_layout.itemAt(1).itemAt(1),
#                                 ga_layout.itemAt(2).itemAt(1)))
#             LOGGER.error('++++ itemAt0.itemAt1widget {}\n     itemAt1itemAt1widget {}\n     itemAt2itemAt1widget {}'.
#                          format(ga_layout.itemAt(0).itemAt(1).widget(),
#                                 ga_layout.itemAt(1).itemAt(1).widget(),
#                                 ga_layout.itemAt(2).itemAt(1).widget()))
        elif (len(self.arrays) == 1) and len(self.already_grouped):
            # We want to group an existing GroupedArrays with a regular array
            datasheet = self.arrays.pop()
            grouped_arrays = self.already_grouped.pop()
            grouped_arrays.deleteLater()
            self.container = grouped_arrays.widget()
            self.getGALayout = self.combineArrayAndGroupedArrays
            ga_layout = self.getGALayout(datasheet, grouped_arrays)
            self.setLayout(ga_layout)
            self.setWidget(self.container)
            self.grouped_arrays_nrows = \
                self.container.layout().itemAt(0).itemAt(1).widget().leaf_model.numrows[()]
            self.already_grouped.add(self)
            self.show()
        # This block of code is executed always so functions 
        # self.setLayout and self.setWidget won't need to be set again
        if len(self.already_grouped) > 1:
            grouped_arrays = self.already_grouped.pop()
            LOGGER.error('++++ grouped_arrays{}'.format(grouped_arrays))
#            grouped_arrays.deleteLater()
            self.container = grouped_arrays.widget()
            self.getGALayout = self.combineGroupedArrays
            ga_layout = self.getGALayout(grouped_arrays)
#            self.setLayout(ga_layout)
#            self.setWidget(self.container)
            self.grouped_arrays_nrows = \
                self.container.layout().itemAt(0).itemAt(1).widget().leaf_model.numrows[()]
            self.already_grouped.add(self)
            self.show()

#        self.customizeGroupedViews()
        

    # The following functions define the behavior of GroupedArrays objects:
    # - how they are created from several Datasheet objects
    # - how a single Datasheet object can be added to a GroupedArray object
    # - how they combine together to create a bigger GroupedArrays object
    # - how they are customized
    # - how they are closed
    # - how they are ungrouped

    def combineArrays(self, arrays):
        """Convert a set of array views into a GroupedArray view.
        """
        
        hlayout = QtGui.QHBoxLayout()
        counter = -1
        while arrays:
            datasheet = arrays.pop()
            counter += 1
            title = QtGui.QLabel(datasheet.windowTitle())
            datasheet.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            datasheet.leaf_view.cornerWidget().source_array = datasheet
            vertical_layout = QtGui.QVBoxLayout()
            vertical_layout.addWidget(title)
            vertical_layout.addWidget(datasheet)
            hlayout.addLayout(vertical_layout)
            datasheet.is_checked = datasheet.leaf_view.cornerWidget().checkState()
            self.is_checked = datasheet.is_checked
        return hlayout


    def combineArrayAndGroupedArrays(self, datasheet, grouped_arrays):
        """Convert an Array and a GroupedArray view into a GroupedArray view.
        
        :Parameters:

        - `datasheet`: the Datasheet object being added to the GroupedArrays
        - `grouped_arrays`: the GroupedArrays object where `datasheet` will be
                            added
        """
        
        title = QtGui.QLabel(datasheet.windowTitle())
        datasheet.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        datasheet.leaf_view.cornerWidget().array = datasheet
        vertical_layout = QtGui.QVBoxLayout()
        vertical_layout.addWidget(title)
        vertical_layout.addWidget(datasheet)
        ga_layout = self.container.layout()
        ga_layout.addLayout(vertical_layout)
        self.is_checked = datasheet.leaf_view.cornerWidget().checkState()
        return ga_layout


    def combineGroupedArrays(self, grouped_arrays):
        """Convert an Array view an set of GroupedArrays into a unique GroupedArrays view.
        
        :Parameter grouped_arrays: a set of GroupedArrays views
        """

        ga_layout = self.container.layout()
        while self.already_grouped:
            current_grouped_array = self.already_grouped.pop()
            LOGGER.error('++++ current_grouped_array {}'.format(current_grouped_array))
            widget = current_grouped_array.widget()
            ga_layout.addWidget(widget)
            current_grouped_array.deleteLater()
        return ga_layout

        
    def ungroupArrays(self):
        pass

    def customizeGroupedViews(self):
        """Make the grouped view widget usable.
        
        - All but the leftmost horizontal header views are hidden
        - All but the rightmost verticals scrollbars are hidden
          and connected between them
        
        Beware that horizontal scrollbars cannot be connected easily if the
        number of columns differ for the grouped arrays so we recommend to
        group only arrays with the same number of columns.

        :Parameter sw: the viw (QMdiSubWindow instance) being customized
        """
        
        # The top level layout, a horizontal box layout
        sw_layout = self.widget().layout()
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


    def closeEvent(self, event):
        """ Propagate the event.
        In the process, self.widget().closeEvent will be called
        """
        
        for datasheet in self.views_to_group:
            datasheet.dbt_leaf.hasview = False
            QtGui.QMdiSubWindow.closeEvent(datasheet, event)
        
        if self.vtgui.workspace.subWindowList() == []:
            self.vtgui.dbs_tree_view.setFocus(True)


