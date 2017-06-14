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


"""Plugin that provides columnar organizations for arrays

The plugin let the users to mark several array views (all of them with the
same number of rows) and then display those arrays using a unique widget, one
array next to other. One can think that a set of arrays are displayed as a
table. This seems quite strange to me but is a feature request so I assume
that the plugin will be useful to some users.
"""

__docformat__ = 'restructuredtext'
__version__ = '1.1'
plugin_name = 'Columnar organization of arrays'
comment = ('Rearrange several arrays with the same number of rows and '
           'displays them in a unique widget')

import os.path

import tables

from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import vitables
from vitables.vttables.datasheet import DataSheet
from vitables.plugins.aboutpage import AboutPage

translate = QtWidgets.QApplication.translate

_PLUGIN_FOLDER = os.path.join(os.path.dirname(__file__))


class ArrayColsOrganizer(QtCore.QObject):
    """The class which defines the plugin for columnar organization of arrays.

    It is connected to the core program so that ever time a new view
    is created this class customizes the view if it is required. In
    addition the class triggers the update of the Node menu and
    includes a `helpAbout`method that is used in the Preferences
    dialog to show information about the plugin.

    """

    UID = __name__
    NAME = plugin_name
    COMMENT = comment

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

    def customizeView(self, datasheet):
        """Add a checkbox in the bottom right corner of array views.

        Customization is twofold: add a checkbox to the LeafView and add a
        is_checked` attr to the view. In addition, the checkbox has a
        `source_array` attribute that points to the view containing it.

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
            cb = QtWidgets.QCheckBox(datasheet)
            cb.setToolTip(translate('ArrayColsOrganizer',
                                    "Include this Array in the 'columnar Group'",
                                    'Checkbox tooltip text'))
            datasheet.leaf_view.setCornerWidget(cb)
            # Attributes for retrieving the state of the checkbox from the
            # datasheet being customized
            cb.source_array = datasheet
            datasheet.is_checked = \
                datasheet.leaf_view.cornerWidget().checkState()

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
                'comment': translate('ArrayColsOrganizer',
                                     """
                    <qt><p>Plugin that provides an alternative view for
                    arrays with the same number of rows. <p>
                    The user has to open all the arrays she whishes to see in
                    a unique viewer, and tick their bottom-right corner
                    checkbox.
                    She may then click on the `Node -> Group Arrays`
                    menu entry and these arrays will be grouped
                    in a single sub-window.
                    <p>Note that all ticked arrays must have the same
                    dimensions for the `Group` menu item to enable.</qt>
                    """,
                                     'Text of an About plugin message box')}
        about_page = AboutPage(desc, parent)
        return about_page


class MenuUpdater(QtCore.QObject):
    """Specialized class for modifying the Node menu.
    """

    def __init__(self, parent=None):
        """The constructor method.
        """

        super(MenuUpdater, self).__init__(parent)
        self.vtgui = vitables.utils.getGui()

        # Connect signals to slots
        self.vtgui.node_menu.aboutToShow.connect(self.updateNodeMenu)
        self.vtgui.leaf_node_cm.aboutToShow.connect(self.updateNodeMenu)

    def addEntry(self):
        """Add the `Group Arrays` and `Ungroup Arrays` entries to `Node` menu.
        """

        object_group_icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(_PLUGIN_FOLDER,
                                            'icons/object-group.png'))
        object_group_icon.addPixmap(pixmap,
                                    QtGui.QIcon.Normal,
                                    QtGui.QIcon.On)

        self.group_action = QtWidgets.QAction(
            translate('MenuUpdater',
                      "&Group Arrays",
                      "Group separated arrays with the same number of rows"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey,
            triggered=self.groupArrays,
            icon=object_group_icon,
            statusTip=translate('MenuUpdater',
                                """
                Use a unique widget to display Arrays as if
                they where columns of a Table""",
                                "Status bar text for the Node -> Group Arrays action"))

        object_ungroup_icon = QtGui.QIcon()
        pixmap = QtGui.QPixmap(os.path.join(_PLUGIN_FOLDER,
                                            'icons/object-ungroup.png'))
        object_ungroup_icon.addPixmap(pixmap,
                                      QtGui.QIcon.Normal,
                                      QtGui.QIcon.On)

        self.ungroup_action = QtWidgets.QAction(
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
        vitables.utils.addToMenu(self.vtgui.node_menu, (self.group_action,
                                                        self.ungroup_action))

        # Add the actions to the leaf context menu
        vitables.utils.addToLeafContextMenu(
            (self.group_action, self.ungroup_action))

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
                elif isinstance(view, DataSheet):
                    numrows.append(view.leaf_model.numrows[()])

        self.checked_views = checked_views

        if len(checked_views) == 1:
            if isinstance(checked_views[0], GroupedArrays):
                self.ungroup_action.setEnabled(True)
        elif len(checked_views) > 1:
            if numrows.count(numrows[0]) == len(numrows):
                self.group_action.setEnabled(True)
            else:
                print(translate('MenuUpdater',
                                """\nError: grouping arrays, operation cancelled. """
                                """Not all the selected arrays have the same number """
                                """of rows.""",
                                'An error message in the ArraysColsOrganizer plugin'))

    def groupArrays(self):
        """Group a set of individual arrays into the same view widget.
        """
        GroupedArrays(views=self.checked_views)

    def ungroupArrays(self):
        """Break-up a grouped array into a set of views (one per component).
        """
        GroupedArrays.ungroupArrays(self.checked_views[0])


class GroupedArrays(QtWidgets.QMdiSubWindow):
    """A widget that contains a group of Arrays.
    """

    def __init__(self, parent=None, flags=QtCore.Qt.SubWindow,
                 views=None):
        """The class constructor.
        """

        self.vtgui = vitables.utils.getGui()
        super(GroupedArrays, self).__init__(self.vtgui.workspace, flags)

        # The components from which the GroupedArrays will be made.
        # We use sets instead of lists because there seems to be a
        # problem with my_list.pop(i) when i != -1
        self.arrays = set(views)
        self.already_grouped = set([])
        for i in self.arrays.copy():
            if isinstance(i, GroupedArrays):
                self.already_grouped.add(i)
                self.arrays.remove(i)
        self.arrays = list(self.arrays)
        self.already_grouped = list(self.already_grouped)
        self.pindex = QtCore.QModelIndex()
        # Create a GroupedArrays object from the set of regular arrays
        if (len(self.arrays) > 1):
            self.combineArrays()
        # Combine regular arrays with GroupedArrays
        elif (len(self.arrays) == 1) and len(self.already_grouped):
            self.combineArrayAndGroupedArrays()
        # Combine GroupedArrays (no regular arrays in the way)
        elif len(self.already_grouped) > 1:
            self.combineGroupedArrays()

    # The following functions define the behavior of GroupedArrays objects:
    # - how they are created from several Datasheet objects
    # - how a single Datasheet object can be added to a GroupedArray object
    # - how they combine together to create a bigger GroupedArrays object
    # - how they are customized
    # - how they are closed
    # - how they are ungrouped

    def addVerticalLayout(self, container_layout, datasheet, title=None):
        """Add a vertical layout to the horizontal layout of a GroupArrays.

        This is a helper method.

        :Parameter:
        - `container_layout`: the horizontal layout of the ArraysGroup
        - `datasheet`: the datasheet being added
        """

        if not title:
            title = QtWidgets.QLabel(datasheet.windowTitle())
        datasheet.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.addWidget(title)
        vertical_layout.addWidget(datasheet)
        container_layout.addLayout(vertical_layout)

    def convenienceAttrs(self, datasheet):
        """Helper method for setting some attributes
        """

        self.is_checked = QtCore.Qt.Checked
        nrows = datasheet.leaf_model.numrows[()]
        self.grouped_arrays_nrows = nrows

    def combineArrays(self):
        """Convert a set of array views into a GroupedArray view.
        """

        self.pindex = QtCore.QModelIndex()
        # The widget of this MdiSubWindow
        self.container = QtWidgets.QWidget()

        # Fill the widget with Datasheets arranged in the container layout
        container_layout = QtWidgets.QHBoxLayout()
        while self.arrays:
            # Extract the first datasheet and manipulate it conveniently:
            # get the title, remove the frame and put both of them in a
            # vertical layout
            datasheet = self.arrays.pop()
            self.addVerticalLayout(container_layout, datasheet)
        self.container.setLayout(container_layout)

        # Some convenient attributes
        self.convenienceAttrs(datasheet)

        # Create and customize the MdiSubWindow
        self.setWidget(self.container)
        self.show()
        self.customizeGroupedViews()

    def combineArrayAndGroupedArrays(self):
        """Add an Array to this GroupedArray instance.
        """

        datasheet = self.arrays.pop()
        # Overwrite self with the last GroupedArray instance of the list
        # of grouped arrays but preserve the list of grouped arrays seen
        # by the self object. Calling self.show() won't be required because
        # the GroupedArray is already visible
        self.deleteLater()
        self.pindex = QtCore.QModelIndex()
        grouped_arrays = self.already_grouped[:]
        self = self.already_grouped.pop()
        self.already_grouped = grouped_arrays[:-1]
        self.container = self.widget()
        container_layout = self.container.layout()
        # The datasheet is manipulated conveniently:
        # get the title, remove the frame and put both of them in a
        # vertical layout
        self.addVerticalLayout(container_layout, datasheet)

        # Some convenient attributes
        self.convenienceAttrs(datasheet)

        self.customizeGroupedViews()

    def combineGroupedArrays(self):
        """Convert a set of GroupedArrays into a unique GroupedArrays view.

        :Parameter grouped_arrays: a set of GroupedArrays views
        """

        # Overwrite self with the last GroupedArray instance of the list
        # of grouped arrays but preserve the list of grouped arrays seen
        # by the self object. Calling self.show() won't be required because
        # the GroupedArray is already visible
        self.deleteLater()
        self.pindex = QtCore.QModelIndex()
        grouped_arrays = self.already_grouped[:]
        self = self.already_grouped.pop()
        self.already_grouped = grouped_arrays[:-1]
        self.container = self.widget()
        container_layout = self.container.layout()

        while self.already_grouped:
            ga = self.already_grouped.pop(-1)
            hlayout = ga.widget().layout()
            first_datasheet = hlayout.itemAt(0).itemAt(1).widget()
            for i in range(hlayout.count()):
                vl = hlayout.itemAt(i)
                title = vl.itemAt(0).widget()
                datasheet = vl.itemAt(1).widget()
                self.addVerticalLayout(container_layout, datasheet, title)
            ga.deleteLater()
#        self.repaint()

        # Some convenient attributes
        self.convenienceAttrs(first_datasheet)

        self.customizeGroupedViews()

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

        # This instance will be the first GroupedArray instance of the set
        # Calling self.show() won't be required because the GroupedArray is
        # already visible
        self.container = self.widget()
        container_layout = self.container.layout()

        # The items contained in the container layout are QVBoxLAyout layout
        # boxes. These vertical layouts can contain labels and datasheets:
        # horizontal layout -> vertical layout -> widget item -> label
        #                                     |-> widget item -> datasheet
        datasheets = []
        for i in range(container_layout.count()):
            vl = container_layout.itemAt(i)
            datasheets.append(vl.itemAt(1).widget())

        nd = len(datasheets)
        for i in range(nd):
            datasheets[nd - 1].widget().verticalScrollBar().valueChanged.connect(
                datasheets[i].widget().verticalScrollBar().setValue)
            if i < (nd - 1):
                datasheets[i].widget().verticalScrollBar().hide()
                datasheets[i].widget().setCornerWidget(None)
                datasheets[i + 1].widget().verticalHeader().hide()

    def closeEvent(self, event):
        """ Propagate the close event.
        In the process, self.widget().closeEvent will be called
        """

        sw_layout = self.widget().layout()
        vl_count = sw_layout.count()
        for i in range(vl_count):
            layout = sw_layout.itemAt(i)
            datasheet = layout.itemAt(1).widget()
            datasheet.dbt_leaf.hasview = False
            self.vtgui.updateActions()
            datasheet.close()
            layout.deleteLater()

        self.deleteLater()
        QtWidgets.QMdiSubWindow.closeEvent(self, event)
        if self.vtgui.workspace.subWindowList() == []:
            self.vtgui.dbs_tree_view.setFocus(True)

    def ungroupArrays(self):
        """Break-up a GroupedArrays object into its individual components.
        """

        for view in self.vtgui.workspace.subWindowList():
            if isinstance(view, GroupedArrays):
                self = view
                break
        sw_layout = self.widget().layout()
        vl_count = sw_layout.count()
        for i in range(vl_count):
            layout = sw_layout.itemAt(i)
            title = layout.itemAt(0).widget().text()
            datasheet = layout.itemAt(1).widget()
            datasheet.setWindowFlags(QtCore.Qt.SubWindow)
            datasheet.setWindowTitle(title)
            datasheet.setParent(self.vtgui.workspace)
            datasheet.widget().verticalScrollBar().show()
            datasheet.widget().verticalHeader().show()
            cb = QtWidgets.QCheckBox(datasheet)
            cb.setToolTip(translate('GroupedArrays',
                                    "Group Arrays into a unique view",
                                    'Checkbox tooltip'))
            datasheet.leaf_view.setCornerWidget(cb)
            # Attributes for retrieving the state of the checkbox from the
            # datasheet being customized
            cb.source_array = datasheet
            datasheet.leaf_view.cornerWidget().setCheckState(QtCore.Qt.Checked)
            datasheet.is_checked = \
                datasheet.leaf_view.cornerWidget().checkState()
            datasheet.show()
            layout.deleteLater()
        self.deleteLater()
        self.vtgui.workspace.removeSubWindow(self)
