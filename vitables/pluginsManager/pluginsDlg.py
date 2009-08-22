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

"""Dialog for managing plugins. The user can add/remove plugins paths and
enable/disable found plugins. Enabled plugins are automatically loaded if
possible.
"""

__docformat__ = 'restructuredtext'
_context = 'PluginsDlg'

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils
from vitables.pluginsManager import pluginsUI

class PluginsDlg(QDialog, pluginsUI.Ui_PluginsDialog):
    """
    A dialog for managing plugins.

    The dialog layout looks like this::

        root
            label + combobox + button + button
            listbox +  2 buttons stacked vertically + listbox
            Ok + Cancel

    """

    def __init__(self):
        """ctor.
        """

        #
        # Create the dialog and customise the content of some widgets
        #
        QDialog.__init__(self, qApp.activeWindow())
        self.setupUi(self)

        self.disabled_tree.setColumnHidden(1, True)
        self.enabled_tree.setColumnHidden(1, True)
        self.disabled_tree.setHeaderHidden(True)
        self.enabled_tree.setHeaderHidden(True)

        self.show()

        self.vtapp = vitables.utils.getVTApp()
        self.manager = self.vtapp.plugins_mgr

        # Add items to the list of plugins paths
        for item in self.manager.plugins_paths:
            self.paths_lw.addItem(item)
        self.paths_lw.selectionModel().clearSelection()

        # Add items to the list of enabled plugins
        for item in self.manager.enabled_plugins:
            self.addTreeItem(item, tree='enabled')
        self.enabled_tree.selectionModel().clearSelection()

        # Add items to the list of disabled plugins
        for item in self.manager.disabled_plugins:
            self.addTreeItem(item, tree='disabled')
        self.disabled_tree.selectionModel().clearSelection()

        # Connect signals to slots
        self.connect(self.buttons_box, SIGNAL('accepted()'), 
            self.slotAccept)
        self.connect(self.buttons_box, SIGNAL('rejected()'),
            self.slotCancel)
        self.connect(self.buttons_box, SIGNAL('helpRequested()'),
            QWhatsThis.enterWhatsThisMode)
        self.connect(self.new_button, SIGNAL('clicked()'), 
            self.slotAddPath)
        self.connect(self.remove_button, SIGNAL('clicked()'),
            self.slotRemovePath)
        self.connect(self.load_button, SIGNAL('clicked()'),
            self.slotEnablePlugin)
        self.connect(self.unload_button, SIGNAL('clicked()'),
            self.slotDisablePlugin)
        selection_changed = SIGNAL('itemSelectionChanged()')
        self.connect(self.disabled_tree, selection_changed, \
            self.slotUpdateButton)
        self.connect(self.enabled_tree, selection_changed, \
            self.slotUpdateButton)
        self.connect(self.paths_lw, selection_changed, \
            self.slotUpdateButton)

        # Update the GUI
        self.slotUpdateButton('all')


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


    def addTreeItem(self, item, tree='enabled'):
        """Add an item to a tree widget containing a list of plugins.

        For convenience lists of plugins are not displayed in a
        ListWidget but in a TreeWidget with the plugin path stored in a
        hidden column.

        Sometimes added items are displayed disabled:

            - enabled plugins that cannot be loaded at start time
            - plugins enabled by user during a session (they will not be
              loaded immediately but in the next session)
            - plugins disabled by user during a session will remain
              loaded until the session closes

        :Parameters:

        - item: the plugin UID being added
        - tree: the TreeWidget where the plugin will be added
        """

        (folder, name) = item.split('#@#')
        if tree == 'enabled':
            tree = self.enabled_tree
        else:
            tree = self.disabled_tree
        tree_item = QTreeWidgetItem(tree)
        tree_item.setText(0, name)
        tree_item.setText(1, folder)
        tree.addTopLevelItem(tree_item)
        # If a plugin in the list of enabled plugins is not loaded it
        # will appear disabled in the enabled plugins list. In the same
        # spirit, if a plugin in the list of disabled plugins is still
        # loaded it will appear disabled in the list of disabled plugins
        if tree == self.enabled_tree and \
            item not in self.manager.loaded_plugins.keys():
            tree_item.setDisabled(True)
        if tree == self.disabled_tree and \
            item in self.manager.loaded_plugins.keys():
            tree_item.setDisabled(True)


    def slotAccept(self):
        """OK button clicked.

        When dialog is closed the Plugins Manager is updated.
        """

        # Update the plugins_path variable
        plugins_paths = []
        for row in range(self.paths_lw.count()):
            path = unicode(self.paths_lw.item(row).text())
            plugins_paths.append(path)
        self.manager.plugins_paths = plugins_paths

        # Update the enabled plugins variable
        enabled_plugins = []
        for row in range(self.enabled_tree.topLevelItemCount()):
            name = unicode(self.enabled_tree.topLevelItem(row).text(0))
            folder = unicode(self.enabled_tree.topLevelItem(row).text(1))
            enabled_plugins.append('%s#@#%s' % (folder, name))
        self.manager.enabled_plugins = enabled_plugins

        # Update other info about plugins
        self.manager.updatePluginsInfo()

        # Close the dialog
        self.updateTypes()
        self.accept()


    def slotCancel(self):
        """Cancel button clicked.
        """

        self.updateTypes()
        self.reject()


    def slotAddPath(self):
        """New button clicked.
        """

        folder = QFileDialog.getExistingDirectory()
        if not unicode(folder) in self.manager.plugins_paths:
            self.manager.plugins_paths.append(folder)
            self.paths_lw.addItem(folder)


    def slotRemovePath(self):
        """Remove button clicked.
        """

        current = self.paths_lw.currentRow()
        self.paths_lw.takeItem(current)


    def slotEnablePlugin(self):
        """Load button clicked.
        """

        # The widget selection model is single selection so the selected
        # item is always the current item (opposite is not true)
        current = self.disabled_tree.currentItem()
        index = self.disabled_tree.indexOfTopLevelItem(current)
        item = '%s#@#%s' % (unicode(current.text(1)), unicode(current.text(0)))
        self.addTreeItem(item, tree='enabled')
        self.disabled_tree.takeTopLevelItem(index)
        del current


    def slotDisablePlugin(self):
        """Unload button clicked.
        """

        # The widget selection model is single selection so the selected
        # item is always the current item (opposite is not true)
        current = self.enabled_tree.currentItem()
        index = self.enabled_tree.indexOfTopLevelItem(current)
        item = '%s#@#%s' % (unicode(current.text(1)), unicode(current.text(0)))
        self.addTreeItem(item, tree='disabled')
        self.enabled_tree.takeTopLevelItem(index)
        del current


    def slotUpdateButton(self, button=None):
        """Enable/disable the given button.
        """

        buttons = (self.remove_button, self.load_button, self.unload_button)

        # Map item widgets with buttons
        widget2button = {}
        key = unicode(self.paths_lw.objectName())
        widget2button[key] = self.remove_button
        key = unicode(self.enabled_tree.objectName())
        widget2button[key] = self.unload_button
        key = unicode(self.disabled_tree.objectName())
        widget2button[key] = self.load_button

        # This is enforced every time the dialog is displayed
        if button == 'all':
            # Initial update
            for item in buttons:
                item.setEnabled(False)
            return

        # This happens every time the selected item changes
        widget = self.sender()
        button = widget2button[unicode(widget.objectName())]
        # If there is a selected item in the widget then the binded
        # button is enabled
        if widget.selectedItems() != []:
            button.setEnabled(True)
        else:
            button.setEnabled(False)


    def updateTypes(self):
        """Sanitize the type of variables stored as config. settings.

        `plugins_paths` and `enabled_plugins` vars must be returned to
        the application as QStringList in order to store them properly
        as configuration settings when application quits.
        """

        if isinstance(self.manager.plugins_paths, list):
            self.manager.plugins_paths = QStringList(self.manager.plugins_paths)

        if isinstance(self.manager.enabled_plugins, list):
            self.manager.enabled_plugins = \
                QStringList(self.manager.enabled_plugins)
