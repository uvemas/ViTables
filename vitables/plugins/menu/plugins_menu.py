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

"""This plugin creates a Plugins menu and adds an item to it for each 
active plugin. Selecting these menu items will bring up a short About 
Plugin dialog with the details of the plugin.
"""

__docformat__ = 'restructuredtext'
_context = 'PluginsMenu'
__version__ = '0.1'
plugin_class = 'PluginsMenu'

import os

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import PLUGINSDIR


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


def setupTextWidget(parent, palette, kind='line'):
    """Create and setup a QLineEdit widget.
    """

    if kind == 'line':
        widget = QtGui.QLineEdit(parent)
    else:
        widget = QtGui.QTextEdit(parent)
    widget.setReadOnly(True)
    widget.setPalette(palette)
    return widget


class PluginsMenu(QtCore.QObject):
    """Add a Plugins menu to the ViTables menubar.
    """

    def __init__(self):
        """The class constructor.
        """

        QtCore.QObject.__init__(self)

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return

        # Create the Plugins menu and insert it before the Help menu
        self.plugins_menu = QtGui.QMenu(trs("&Plugins", 
            'The Plugins menu entry'))
        for menu in self.vtapp.menuBar().findChildren(QtGui.QMenu):
            if menu.objectName() == 'help_menu':
                self.vtapp.menuBar().insertMenu(menu.menuAction(), 
                    self.plugins_menu)

        # The Plugins menu cannot be populated without knowing which 
        # plugins are loaded so we have to wait until the convenience
        # pluginsLoaded signal is emitted
        self.connect(self.vtapp, QtCore.SIGNAL('pluginsLoaded'), 
            self.populateMenu)


    def populateMenu(self):
        """Populate the Plugins menu.
        """

        loaded_plugins = self.vtapp.plugins_mgr.loaded_plugins
        plugins_keys = loaded_plugins.keys()
        menu_key = os.path.join(PLUGINSDIR, 'menu#@#plugins_menu')
        plugins_keys.remove(menu_key)
        plugins_keys.insert(0, menu_key)

        # Create a QAction for every loaded plugin
        for key in plugins_keys:
            pg_instance = loaded_plugins[key]
            if hasattr(pg_instance, 'helpAbout'):
                slot = self.showInfo
                name = pg_instance.helpAbout()['plugin_name']
            else:
                slot = self.noInfo
                name = key.split('#@#')[1]
            action = QtGui.QAction(name, self.plugins_menu)
            action.setObjectName(key)
            self.plugins_menu.addAction(action)
            self.connect(action, QtCore.SIGNAL('triggered()'), 
                slot)


    def helpAbout(self):
        """Brief description of the plugin."""

        # Text to be displayed
        about_text = trs(
            """<qt>
            <p>This plugin inserts a <b>Plugins</b> menu in the 
            ViTables menu bar and adds an entry to it for each active 
            plugin. Selecting these menu entries will bring up a short 
            <b>About plugin</b> dialog with a brief description of the
            plugin.
            </qt>""",
            'Text of an About plugin message box')

        descr = dict(module_name='plugins_menu.py', 
            folder=os.path.join(PLUGINSDIR, 'menu'), 
            version=__version__, 
            plugin_name='Plugins menu', 
            author='Vicent Mas <vmas@vitables.org>', 
            descr=about_text)

        return descr


    def noInfo(self):
        """
        Message box with a 'No information available' message.
        """

        # Text to be displayed
        about_text = trs(
            "Sorry, there is not available information for this plugin.",
            'Text of the About Plugin message box')

        title = trs('About plugin', 
            'Title for an About plugin message box')

        QtGui.QMessageBox.about(self.vtapp, title, about_text)


    def showInfo(self):
        """Show a dialog with info about a plugin.
        """

        action = self.sender()
        action_name = unicode(action.objectName())
        descr = self.vtapp.plugins_mgr.loaded_plugins[action_name].helpAbout()
        info_dlg = QtGui.QDialog(self.vtapp)
        info_dlg.setWindowTitle(trs('About plugin', 'A dialog title'))

        label1 = QtGui.QLabel(trs('Module name:', 'Label text'), info_dlg)
        label2 = QtGui.QLabel(trs('Folder:', 'Label text'), info_dlg)
        label3 = QtGui.QLabel(trs('Plugin name:', 'Label text'), info_dlg)
        label4 = QtGui.QLabel(trs('Version:', 'Label text'), info_dlg)
        label5 = QtGui.QLabel(trs('Author:', 'Label text'), info_dlg)
        label6 = QtGui.QLabel(trs('Description:', 'Label text'), info_dlg)

        palette = QtGui.QPalette(QtGui.qApp.palette())
        palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, 
            palette.window().color())
        field1 = setupTextWidget(info_dlg, palette)
        field1.setText(descr['module_name'])
        field2 = setupTextWidget(info_dlg, palette)
        field2.setText(descr['folder'])
        field3 = setupTextWidget(info_dlg, palette)
        field3.setText(descr['plugin_name'])
        field4 = setupTextWidget(info_dlg, palette)
        field4.setText(descr['version'])
        field5 = setupTextWidget(info_dlg, palette)
        field5.setText(descr['author'])
        field6 = setupTextWidget(info_dlg, palette, kind='text')
        field6.setText(descr['descr'])

        button_box = QtGui.QDialogButtonBox(info_dlg)
        button_box.addButton(QtGui.QDialogButtonBox.Ok)
        grid = QtGui.QGridLayout(info_dlg)
        grid.addWidget(label1, 0, 0)
        grid.addWidget(field1, 0, 1)
        grid.addWidget(label2, 1, 0)
        grid.addWidget(field2, 1, 1)
        grid.addWidget(label3, 2, 0)
        grid.addWidget(field3, 2, 1)
        grid.addWidget(label4, 3, 0)
        grid.addWidget(field4, 3, 1)
        grid.addWidget(label5, 4, 0)
        grid.addWidget(field5, 4, 1)
        grid.addWidget(label6, 5, 0)
        grid.addWidget(field6, 5, 1)
        grid.addWidget(button_box, 6, 1)

        self.connect(button_box, QtCore.SIGNAL('accepted()'), 
            info_dlg.close)
        info_dlg.show()




