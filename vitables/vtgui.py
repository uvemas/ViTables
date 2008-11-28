# -*- coding: utf-8 -*-

########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008 Vicent Mas. All rights reserved
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
#
#       $Source$
#       $Id: vtgui.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""Here is defined the vtgui module.

Classes:

* Logger(qt.QTextEdit)
* VTGUI(qt.QMainWindow)

Methods:

* Logger.__init__(self, parent)
* Logger.write(self, text)
* Logger.createPopupMenu(self, pos)
* Logger.updateEditMenu(self)
* Logger.disableNodeCopy(self)
* Logger.enableNodeCopy(self)
* Logger.focusInEvent(self, e)
* Logger.focusOutEvent(self, e)
* Logger.eventFilter(self, w, e)
* VTGUI.__init__(self, parent)
* VTGUI.__tr(self, source, comment=None)
* VTGUI.makeGUI(self)
* VTGUI.initPopups(self)
* VTGUI.initMenuBar(self)
* VTGUI.initToolBar(self)
* VTGUI.initStatusBar(self)
* VTGUI.closeEvent(self, event)
* VTGUI.eventFilter(self, w, e)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sys, os

import qt

import vitables.utils
from  vitables.preferences import vtconfig
from vitables.treeEditor.treeView import TreeView

class Logger(qt.QTextEdit):
    """
    Logger that receives all informational application messages.

    All messages delivered by application to user are displayed in the
    logger area. This messages include the status of user requested
    operations, the result of this operations, and also error messages.
    This is possible because the class reimplement the write() method,
    so it can be used to catch both, sys.stdout an sys.stderr, just by
    redirecting them to an instance of this class.
    """


    def __init__(self, parent):
        qt.QTextEdit.__init__(self, parent)
        self.setTextFormat(qt.Qt.PlainText)
        self.setReadOnly(1)
        self.setMinimumHeight(50)
        self.setLineWidth(1)
        self.defaultFrame = self.frameStyle()


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('Logger', source, comment).latin1()


    def write(self, text):
        """
        The standard output and the standard error are redirected to an
        instance of Logger so we must implement a write method in order
        to display the catched messages.

        The implementation is done via QTextEdit.append method because
        this method adds the text at the end of the console so, even if
        the user clicks somewhere in the console or there is selected
        text, the printed text will not mess the console.

        :Parameter text: the text being written
        """

        currentColor = self.color()
        if text in ['\n', '\r\n']:
            return
        if text.startswith('\nError: '):
            self.setColor(qt.QColor('red'))
        elif text.startswith('\nWarning: '):
            self.setColor(qt.QColor(243, 137, 8))
        self.append(text)
        # Warning! Append() doesn't change the cursor position
        # Because we want to reset the current color **at the end** of
        # the console in order to give the proper color to new messages
        # we must update the cursor position **before** the current
        # color is reset
        self.moveCursor(qt.QTextEdit.MoveEnd, 0)
        self.setColor(currentColor)


    def createPopupMenu(self, pos):
        """
        Popup the contextual logger menu.
        
        This method overwrites ``QTextEdit.createPopupMenu`` method.
        """

        # Make the menu
        self.editMenu = qt.QPopupMenu(self)
        self.editMenu.insertItem(self.__tr("&Copy", 'Logger menu entry'),
            self, qt.SLOT('copy()'),
            qt.QKeySequence('CTRL+C'), 100)
        self.editMenu.insertItem(self.__tr("Select &All", 'Logger menu entry'),
            self, qt.SLOT('selectAll()'),
            qt.QKeySequence(), 200)
        self.editMenu.insertItem(self.__tr("Cl&ear All", 'Logger menu entry'),
            self, qt.SLOT('clear()'),
            qt.QKeySequence(), 300)
        self.updateEditMenu()
        self.connect(self.editMenu, qt.SIGNAL('aboutToShow()'),
            self.updateEditMenu)
        self.connect(self.editMenu, qt.SIGNAL('aboutToShow()'),
            self.disableNodeCopy)
        self.connect(self.editMenu, qt.SIGNAL('aboutToHide()'),
            self.enableNodeCopy)

        # Popup the menu
        self.editMenu.resize(self.editMenu.sizeHint())
        #y = self.y() - self.contentsHeight() + self.visibleHeight() + 1
        self.editMenu.popup(pos)

        # Destroy the menu (this is a MUST)
        del self.editMenu


    def updateEditMenu(self):
        """Update items availability when the menu is about to be shown."""

        # QTextEdit.createPopupMenu(self, pos)
        if self.hasSelectedText():
            # Copy is enabled
            self.editMenu.setItemEnabled(100, 1)
        else:
            # Copy is disabled
            self.editMenu.setItemEnabled(100, 0)
            
        if self.length():
            # Clear and Select All are enabled
            self.editMenu.setItemEnabled(200, 1)
            self.editMenu.setItemEnabled(300, 1)
        else:
            # Clear and Select All are disabled
            self.editMenu.setItemEnabled(200, 0)
            self.editMenu.setItemEnabled(300, 0)


    def disableNodeCopy(self):
        """
        Disable the ``Node --> Copy`` action.
        
        This method is called whenever the logger gets keyboard focus
        or its contextual menu is shown.
        """
        # Save the current status of the node copy action
        self.nodeCopyEnabled = self.nodeCopyAction.isEnabled()
        self.nodeCopyAction.setEnabled(0)


    def enableNodeCopy(self):
        """
        Restore the ``Node --> Copy`` action.
        
        This method is called whenever the logger loose keyboard focus
        or its contextual menu is hiden.
        """
        # Restore the initial status of the copy node action
        self.nodeCopyAction.setEnabled(self.nodeCopyEnabled)


    def focusInEvent(self, e):
        """Disable the ``Node --> Copy`` action if the logger has the keyboard focus."""

        self.disableNodeCopy()
        self.setLineWidth(1)
        self.setFrameStyle(qt.QFrame.StyledPanel|qt.QFrame.Plain)
        pal = self.palette()
        pal.setColor(qt.QColorGroup.Foreground, qt.Qt.darkBlue)
        self.setPalette(pal)
        qt.QTextEdit.focusInEvent(self, e)


    def focusOutEvent(self, e):
        """
        Restore the ``Node --> Copy`` action to the status it had when 
        logger got keyboard focus.
        """

        self.enableNodeCopy()
        self.setFrameStyle(self.defaultFrame)
        self.setLineWidth(1)
        qt.QTextEdit.focusOutEvent(self, e)


    def eventFilter(self, w, e):
        if e.type() == qt.QEvent.ContextMenu:
            pos = e.globalPos()
            self.createPopupMenu(pos)
            return True
        else:
            return qt.QTextEdit.eventFilter(self, w, e)


class VTGUI(qt.QMainWindow):
    """This is the application main window."""


    def __init__(self, parent):
        """Creates the central widget of the application main window.

        The widget creation is divided in several steps:

        - icons
        - screen regions
        - menus
        - menu bar
        - tool bar
        - status bar

        :Parameter parent: the application itself, i.e. an instance of `VTApp`.
        """

        qt.QMainWindow.__init__(self)

        self.vtapp = parent
        self.iconsDictionary = vitables.utils.getIcons()

        self.setCaption(self.__tr('ViTables %s' % vtconfig.getVersion(),
            'Main window title'))

        #
        # inits the GUI
        #
        self.makeGUI()
        self.initPopups()
        self.logger.nodeCopyAction = self.actions['nodeCopy']
        self.initMenuBar()
        self.initToolBar()
        self.initStatusBar()
        self.setCentralWidget(self.central)
        self.setIcon(self.iconsDictionary[ 'vitables_wm'])


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('VTGUI', source, comment).latin1()


    def makeGUI(self):
        """
        Makes the GUI.

        The main window is divided in 3 regions by splitters.

        * top left region: QListView
        * top right region: QWorkspace
        * bottom region: QTextEdit
        """

        # Every GUI component is attached to an intermediate container
        # that will be the central widget of the main window
        self.central = qt.QWidget(self)
        self.centralLayout = qt.QVBoxLayout(self.central, 10, 6)

        #
        # children widgets
        #

        # vertical splitter divides the screen into 2 regions
        self.vsplitter = qt.QSplitter(qt.Qt.Vertical, self.central)

        # in turn, screen top region is divided by a splitter.
        self.hsplitter = qt.QSplitter(qt.Qt.Horizontal, self.vsplitter)
        self.otLV = TreeView(self.hsplitter, self.vtapp)
        self.workspace = qt.QWorkspace(self.hsplitter)
        self.workspace.setScrollBarsEnabled(1)
        self.workspace.setFocusPolicy(qt.QWidget.StrongFocus)
        self.workspace.installEventFilter(self)

        # screen bottom region contains the logger, where application
        # messages will be shown
        self.logger = Logger(self.vsplitter)

        #
        # Now we customize the behaviour of every screen region
        #

        # top left region of the screen contains a QListView where
        # object trees and filtered tables will be shown
        self.otLV.gui = self  # For my own convenience:-)
        self.otLV.setSorting(-1, 0)
        self.otLV.addColumn(self.__tr('Object tree',
            'Header of the first column of the object tree page'))
        qt.QWhatsThis.add(self.otLV, self.__tr(
            """<qt>
            <h3>The Object Tree ListView</h3>
            This listview shows the object tree, a graphical
            representation<br>of the data hierarchy of the open files.
            </qt>""",
            'WhatsThis help for the tree pane')
            )

        # top right region of the screen contains a QWorkspace, where opened
        # documents will be displayed
        qt.QWhatsThis.add(self.workspace, self.__tr(
            """<qt>
            <h3>The Workspace</h3>
            This is the area where open leaves of the object tree are
            displayed. Many tables and arrays can be displayed
            simultaneously.
            <p>The diferent views can be tiled as a mosaic or stacked as
            a cascade.
            </qt>""",
            'WhatsThis help for the workspace')
            )

        # bottom screen region
        qt.QWhatsThis.add(self.logger, self.__tr(
            """<qt>
            <h3>The Logger</h3>
            This is the screen region where info about the currently
            selected item is displayed. It also logs the result of all
            operations requested by the user.
            <p>Also execution errors and exceptions are logged in the
            console.
            </qt>""",
            'WhatsThis help for the logger')
            )

        #
        # Finally we add children widgets to root widget layout in order
        # to get them properly displayed
        #

        self.centralLayout.addWidget(self.vsplitter)


    def initPopups(self):
        """
        Init the popup menus and toolbars.

        Popus are made of actions, items and separators.
        The action definition is given by a list with the structure::

            [(actionID, actionArgs, actionText),...]

        where:

        * ``actionID`` is the action identifier.
        * ``actionArgs``
          is a set of arguments for the ``QAction()`` method.
        * ``actionText`` is the status tip associated to the action

        Looping over these definitions we construct the actions and
        add them to the popup menu in a very general maner

        This method provides actions for the following popups
        ``File, Node, Leaf, Windows, Tools, Help``
        and for the toolbars ``File, Node, Help``
        """

        self.actions = {}

        #########################################################
        #
        # 					File menu
        #
        #########################################################

        self.fileMenu = qt.QPopupMenu()

        # fileMenu icons and actions
        fileNewIcon = self.iconsDictionary['filenew']
        fileOpenIcon = self.iconsDictionary['fileopen']
        fileCloseIcon = self.iconsDictionary['fileclose']
        fileSaveAsIcon = self.iconsDictionary['filesaveas']
        fileExitIcon = self.iconsDictionary['exit']

        self.fileMenuActions = [
            ('fileNew',
                fileNewIcon,
                self.__tr('&New', 'File --> New'),
                qt.QKeySequence('CTRL+N'),
                self,
                self.__tr('Create a new file',
                    'Status bar text for the File --> New action')),

            ('fileOpen',
                fileOpenIcon,
                self.__tr('&Open...', 'File --> Open'),
                qt.QKeySequence('CTRL+O'),
                self,
                'fileOpen',
                self.__tr('Open an existing file',
                    'Status bar text for the File --> Open action')),

            ('fileClose',
                fileCloseIcon,
                self.__tr('&Close', 'File --> Close'),
                qt.QKeySequence('CTRL+W'),
                self,
                self.__tr('Close file',
                    'Status bar text for the File --> Close action')),

            ('fileCloseAll',
                self.__tr('Close &All', 'File --> Close All'),
                qt.QKeySequence(''),
                self,
                self.__tr('Close all files',
                    'Status bar text for the File --> Close All action')),

            ('fileSaveAs',
                fileSaveAsIcon,
                self.__tr('&Save as...', 'File --> Save As'),
                qt.QKeySequence('CTRL+SHIFT+S'),
                self,
                self.__tr('Save a renamed copy of a file',
                    'Status bar text for the File --> Save As action')),

            ('fileExit',
                fileExitIcon,
                self.__tr('E&xit', 'File --> Exit'),
                qt.QKeySequence('CTRL+Q'),
                self,
                self.__tr('Exit the application',
                    'Status bar text for the File --> Exit action'))
        ]
        # Add actions/items/separators to menu
        for t in self.fileMenuActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions[ID].addTo(self.fileMenu)
        self.actions['fileOpen'].setToolTip(self.__tr("""Click to open a """
            """file\nClick and hold to open a recent file""",
            'File toolbar --> Open Recent Files'))

        self.openRecentSubmenu = qt.QPopupMenu()
        self.fileMenu.insertItem(self.__tr('Open R&ecent Files',
            'File --> Open Recent Files'),
            self.openRecentSubmenu, 0, 2)

        self.fileMenu.insertSeparator(3)
        self.fileMenu.insertSeparator(6)
        self.fileMenu.insertSeparator(self.fileMenu.count() - 1)

        #########################################################
        #
        # 					Node menu
        #
        #########################################################

        self.nodeMenu = qt.QPopupMenu()

        nodePropertiesIcon = self.iconsDictionary['info']
        nodeNewIcon = self.iconsDictionary['folder_new']
        nodeCutIcon = self.iconsDictionary['editcut']
        nodeCopyIcon = self.iconsDictionary['editcopy']
        nodeDeleteIcon = self.iconsDictionary['editdelete']
        nodePasteIcon = self.iconsDictionary['editpaste']

        self.nodeMenuActions = [
            ('nodeOpen',
                self.__tr('&Open view', 'Node --> Open View'),
                qt.QKeySequence('CTRL+SHIFT+O'),
                self,
                self.__tr('Display the node contents in a tabular view',
                    'Status bar text for the Node --> Open View action')),

            ('nodeClose',
                self.__tr('C&lose view', 'Node --> Close View'),
                qt.QKeySequence('CTRL+SHIFT+W'),
                self,
                self.__tr('Close the view of the node',
                    'Status bar text for the Node --> Close View action')),

            ('nodeProperties',
                nodePropertiesIcon,
                self.__tr('Prop&erties...', 'Node --> Properties'),
                qt.QKeySequence('CTRL+I'),
                self,
                self.__tr('Show the properties dialog for the node',
                    'Status bar text for the Node --> Properties action')),

            ('nodeNew',
                nodeNewIcon,
                self.__tr('&New group...', 'Node --> New group'),
                qt.QKeySequence('CTRL+SHIFT+N'),
                self,
                self.__tr('Create a new group under the selected node',
                    'Status bar text for the Node --> New group action')),

            ('nodeRename',
                self.__tr('&Rename...', 'Node --> Rename'),
                qt.QKeySequence('CTRL+R'),
                self,
                self.__tr('Rename the selected node',
                    'Status bar text for the Node --> Rename action')),

            ('nodeCut',
                nodeCutIcon,
                self.__tr('Cu&t', 'Node --> Cut'),
                qt.QKeySequence('CTRL+X'),
                self,
                self.__tr('Cut the selected node and place it in the X clipboard',
                    'Status bar text for the Node --> Cut action')),

            ('nodeCopy',
                nodeCopyIcon,
                self.__tr('&Copy', 'Node --> Copy'),
                qt.QKeySequence('CTRL+C'),
                self,
                self.__tr('Copy the selected node to the X clipboard',
                    'Status bar text for the Node --> Copy action')),

            ('nodePaste',
                nodePasteIcon,
                self.__tr('&Paste', 'Node --> Paste'),
                qt.QKeySequence('CTRL+V'),
                self,
                self.__tr('Paste the node saved in the X clipboard',
                    'Status bar text for the Node --> Paste action')),

            ('nodeDelete',
                nodeDeleteIcon,
                self.__tr('&Delete', 'Node --> Delete'),
                qt.QKeySequence(qt.Qt.Key_Delete),
                self,
                self.__tr('Delete the selected node',
                    'Status bar text for the Node --> Delete action'))
        ]

        # Add actions to menu
        for t in self.nodeMenuActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions[ID].addTo(self.nodeMenu)

        self.nodeMenu.insertSeparator(3)

        #########################################################
        #
        # 					Leaf menu
        #
        #########################################################

        self.leafMenu = qt.QPopupMenu()

        # leafMenu actions
        self.leafMenuActions = []

        # Add actions to menu
        for t in self.leafMenuActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions[ID].addTo(self.leafMenu)

        #########################################################
        #
        # 					Query menu
        #
        #########################################################

        self.queryMenu = qt.QPopupMenu()

        queryFilterIcon = self.iconsDictionary['new_filter']

        self.queryMenuActions = [
            ('queryNew',
            queryFilterIcon,
                self.__tr('&New...', 'Query --> New...'),
                qt.QKeySequence(''),
                self,
                self.__tr('Create a new filter for the selected dataset',
                    'Status bar tip for the Query --> New... action')),

##            ('queryList',
##                self.__tr('&List', 'Query --> List'),
##                QKeySequence(''),
##                self,
##                self.__tr('List the currently available filters',
##                    'Status bar tip for the Query --> List action')),
##
#            ('queryDelete',
#                self.__tr('&Delete', 'Query --> Delete'),
#                QKeySequence(''),
#                self,
#                self.__tr('Delete the selected filter',
#                    'Status bar tip for the Query --> Delete action')),
#
            ('queryDeleteAll',
                self.__tr('Delete &All', 'Query --> Delete All'),
                qt.QKeySequence(''),
                self,
                self.__tr('Remove all filters',
                    'Status bar tip for the Query --> Delete All'))
        ]

        # Add actions to menu
        for t in self.queryMenuActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions[ID].addTo(self.queryMenu)

        self.queryMenu.insertSeparator(1)

        #########################################################
        #
        # 					Windows menu
        #
        #########################################################

        # This menu is a special case due to its dynamic nature.
        # The menu contents depend on the number of existing views.
        # In order to track changes and keep updated the menu, it is reloaded
        # every time it is about to be displayed. This goal is achieved using
        # signal/slot mechanism (see code below).

        self.windowsMenu = qt.QPopupMenu()
        self.windowsMenu.setCheckable(1)

        # windowMenuActions
        self.windowsMenuActions = [
            ('windowCascade',
                self.__tr('&Cascade', 'Windows --> Cascade'),
                qt.QKeySequence(''),
                self,
                self.__tr('Arranges open windows in a cascade pattern',
                    'Status bar text for the Windows --> Cascade action')),

            ('windowTile',
                self.__tr('&Tile', 'Windows --> Tile'),
                qt.QKeySequence(''),
                self,
                self.__tr('Arranges open windows in a tile pattern',
                    'Status bar text for the Windows --> Tile action')),

            ('windowClose',
                self.__tr('C&lose', 'Windows --> Close'),
                qt.QKeySequence(''),
                self,
                self.__tr('Close window',
                    'Status bar text for the Windows --> Close action')),

            ('windowCloseAll',
                self.__tr('Close &All', 'Windows --> Close All'),
                qt.QKeySequence(''),
                self,
                self.__tr('Close all windows',
                    'Status bar text for the Windows --> Close All action'))
        ]

        # Grouping Windows menu actions
        # Add actions/items/separators to menu
        self.actions['windowsActionGroup'] = qt.QActionGroup(self, None, 0)
        for t in self.windowsMenuActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions['windowsActionGroup'].add(self.actions[ID])
            self.actions[ID].addTo(self.windowsMenu)
        self.windowsMenu.insertSeparator()

        # This marks the end of the unmutable part of the menu
        self.lastCoreItemPosition = self.windowsMenu.count() - 1

        #########################################################
        #
        # 					Tools menu
        #
        #########################################################

        self.toolsMenu = qt.QPopupMenu()
        self.hideToolBarSubmenu = qt.QPopupMenu()
        self.hideToolBarSubmenu.setCheckable(1)

        toolsPreferencesIcon = self.iconsDictionary['appearance']

        self.toolsMenuActions = [
            ('toolsUserOptions',
                toolsPreferencesIcon,
                self.__tr( '&Preferences...', 'Tools --> Preferences'),
                qt.QKeySequence(''),
                self,
                self.__tr('Configure the aplication',
                    'Status bar text for the Tools --> Preferences action'))
        ]

        self.toolsHideActions = [
            ('toolsHideFileToolbar',
                self.__tr( '&File', 'Tools --> Toolbars... --> File'),
                qt.QKeySequence(''),
                self,
                self.__tr('Show/hide the File toolbar',
                    """Status bar text for the Tools --> Toolbars... --> """
                    """File action""")),

            ('toolsHideNodeToolbar',
                self.__tr( '&Node', 'Tools --> Toolbars... --> Node'),
                qt.QKeySequence(''),
                self,
                self.__tr('Show/hide the Node toolbar',
                    """Status bar text for the Tools --> Toolbars... --> """
                    """Node action""")),

            ('toolsHideHelpToolbar',
                self.__tr( '&Help', 'Tools --> Toolbars... --> Help'),
                qt.QKeySequence(''),
                self,
                self.__tr('Show/hide the Help toolbar',
                    """Status bar text for the Tools --> Toolbars... --> """
                    """Help action""")),

            ('toolsHideLineUp',
                self.__tr('&Line up', 'Tools --> Toolbars... --> Line up'),
                qt.QKeySequence(''),
                self,
                self.__tr('Line up the toolbars to minimize wasted space',
                    """Status bar text for the Tools --> Toolbars... --> """
                    """Line up action"""))
        ]

        # Add actions to menus
        for t in self.toolsMenuActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions[ID].addTo(self.toolsMenu)

        for t in self.toolsHideActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions[ID].addTo(self.hideToolBarSubmenu)

        self.toolsMenu.insertItem(self.__tr('&Toolbars',
            'Tools --> Show/hide toolbars...'),
            self.hideToolBarSubmenu, 0, 0)
        self.toolsMenu.insertSeparator(1)
        self.hideToolBarSubmenu.insertSeparator(3)
        for pos in range(0,3):
            id = self.hideToolBarSubmenu.idAt(pos)
            self.hideToolBarSubmenu.setItemChecked(id, 1)

        #########################################################
        #
        # 					Help menu
        #
        #########################################################

        self.helpMenu = qt.QPopupMenu()

        helpHelpIcon = self.iconsDictionary['usersguide']

        self.helpMenuActions = [
            ('helpUsersGuide',
                helpHelpIcon,
                self.__tr("&User's Guide", 'Help --> Users Guide'),
                qt.QKeySequence(''),
                self,
                self.__tr('Open a HelpBrowser window',
                    'Status bar text for the Help --> Users Guide action')),

            ('helpAbout',
                self.__tr('&About', 'Help --> About'),
                qt.QKeySequence(''),
                self,
                self.__tr('Display information about ViTables',
                    'Status bar text for the Help --> About action')),

            ('helpAboutQt',
                self.__tr('About &Qt', 'Help --> About Qt'),
                qt.QKeySequence(''),
                self,
                self.__tr('Display information about the Qt library',
                    'Status bar text for the Help --> About Qt action')),

            ('helpVersions',
                self.__tr('Show &Versions', 'Help --> Show Versions'),
                qt.QKeySequence(''),
                self,
                self.__tr('Display version information',
                    'Status bar text for the Help --> Show Versions action')),

            ('helpWhatsThis',
                self.__tr('What\'s &This', 'Help --> Whats This'),
                qt.QKeySequence('SHIFT+F1'),
                self,
                self.__tr('Contextual help',
                    'Status bar text for the Help --> Whats This action'))
        ]

        # Add actions/items/separators to menu
        for t in self.helpMenuActions:
            ID = t[0]
            self.actions[ID] = apply(qt.QAction, t[1:-1])
            self.actions[ID].setStatusTip(t[-1])
            self.actions[ID].addTo(self.helpMenu)
        self.helpMenu.insertSeparator(1)
        self.helpMenu.insertSeparator(5)

        #########################################################
        #
        # 					Contextual menus
        #
        #########################################################
        
        self.rootNodeCM = qt.QPopupMenu()
        self.actions['fileClose'].addTo(self.rootNodeCM)
        self.actions['fileSaveAs'].addTo(self.rootNodeCM)
        self.rootNodeCM.insertSeparator()
        self.actions['nodeProperties'].addTo(self.rootNodeCM)
        self.rootNodeCM.insertSeparator()
        self.actions['nodeNew'].addTo(self.rootNodeCM)
        self.actions['nodeCopy'].addTo(self.rootNodeCM)
        self.actions['nodePaste'].addTo(self.rootNodeCM)
        self.rootNodeCM.insertSeparator()
        self.actions['queryDeleteAll'].addTo(self.rootNodeCM)

        self.groupNodeCM = qt.QPopupMenu()
        self.actions['nodeProperties'].addTo(self.groupNodeCM)
        self.groupNodeCM.insertSeparator()
        self.actions['nodeNew'].addTo(self.groupNodeCM)
        self.actions['nodeRename'].addTo(self.groupNodeCM)
        self.actions['nodeCut'].addTo(self.groupNodeCM)
        self.actions['nodeCopy'].addTo(self.groupNodeCM)
        self.actions['nodePaste'].addTo(self.groupNodeCM)
        self.actions['nodeDelete'].addTo(self.groupNodeCM)

        self.leafNodeCM = qt.QPopupMenu()
        self.actions['nodeOpen'].addTo(self.leafNodeCM)
        self.actions['nodeClose'].addTo(self.leafNodeCM)
        self.leafNodeCM.insertSeparator()
        self.actions['nodeProperties'].addTo(self.leafNodeCM)
        self.leafNodeCM.insertSeparator()
        self.actions['nodeRename'].addTo(self.leafNodeCM)
        self.actions['nodeCut'].addTo(self.leafNodeCM)
        self.actions['nodeCopy'].addTo(self.leafNodeCM)
        self.actions['nodePaste'].addTo(self.leafNodeCM)
        self.actions['nodeDelete'].addTo(self.leafNodeCM)


    def initMenuBar(self):
        """
        Init the menu bar.

        Make popup menus and add them to the menu bar.
        """

        # popups are added to the menu bar
        menuBarItems = [
            (self.__tr('&File', 'The File menu title'), self.fileMenu),
            (self.__tr('&Node', 'The Node menu title'), self.nodeMenu),
##            (self.__tr('&Leaf', 'The Leaf menu title'), self.leafMenu),
            (self.__tr('&Query', 'The Query menu title'), self.queryMenu),
            (self.__tr('&Windows', 'The Windows menu title'), self.windowsMenu),
            (self.__tr('Too&ls', 'The Tools menu title'), self.toolsMenu),
            (self.__tr('&Help', 'The Help menu title'), self.helpMenu)
        ]
        for (label, item) in menuBarItems:
            self.menuBar().insertItem(label, item)


    def initToolBar(self):
        """
        Initializes toolbar.

        The toolbar is made of the toolbars ``File``, ``Node`` and
        ``Help``.
        Individual toolbars are made of a subset of actions of the
        corresponding popup menu.
        All toolbar buttons have been resized to make them more visible.
        """

        # File toolbar
        self.fileToolBar = qt.QToolBar(self, 'File operations')
        self.actions['fileExit'].addTo(self.fileToolBar)
        self.actions['fileNew'].addTo(self.fileToolBar)
        self.actions['fileOpen'].addTo(self.fileToolBar)
        self.actions['fileClose'].addTo(self.fileToolBar)
        self.actions['fileSaveAs'].addTo(self.fileToolBar)
        # The name of a QAction is inherited by its children, which
        # comes in handy here
        fileOpenButton = self.fileToolBar.child('fileOpen_action_button')
        fileOpenButton.setIconSet(self.iconsDictionary['fileopen_popup'])
        fileOpenButton.setPopup(self.openRecentSubmenu)
        # Node toolbar
        self.nodeToolBar = qt.QToolBar(self, 'Node operations')
        self.actions['nodeNew'].addTo(self.nodeToolBar)
        self.actions['nodeCut'].addTo(self.nodeToolBar)
        self.actions['nodeCopy'].addTo(self.nodeToolBar)
        self.actions['nodePaste'].addTo(self.nodeToolBar)
        self.actions['nodeDelete'].addTo(self.nodeToolBar)
        # Help toolbar
        self.helpToolBar = qt.QToolBar(self, "User's guide")
        self.actions['helpUsersGuide'].addTo(self.helpToolBar)
        whatis = qt.QWhatsThis.whatsThisButton(self.helpToolBar)

        # Set the size of toolbuttons to 24x24 (see resources.getIcons method)
        children = self.fileToolBar.children() + self.nodeToolBar.children() +\
            self.helpToolBar.children()
        toolButtons = \
            [child for child in children if child.name().endswith('action_button')]
        for tbutton in toolButtons:
            tbutton.setUsesBigPixmap(1)


    def initStatusBar(self):
        """Init status bar."""

        sb = self.statusBar()
        self.sbNodeInfo = qt.QLabel(sb)
        self.sbNodeInfo.setPaletteBackgroundColor(sb.palette().active().background())
        self.sbNodeInfo.setLineWidth(0)
        self.sbNodeInfo.setFrameStyle(qt.QFrame.NoFrame)
        sb.addWidget(self.sbNodeInfo, 0, 1)
        self.sbNodeInfo.setText(self.__tr('Selected node: ',
            'The Selected node box startup message'))
        sb.message(self.__tr('Ready...',
            'The status bar startup message'))

    def closeEvent(self, event):
        """
        Handle close events.

        Clicking the close button of the main window titlebar causes
        the application quitting immediately, leaving things in a non
        consistent state. This event handler ensures that the needed
        tidy up is done before to quit.
        """

        # Main window close button clicked
        self.vtapp.slotFileExit()


    def eventFilter(self, w, e):
        """Customize the behavior of the workspace contextual menu."""

        # QWorkspace doesn't have a contextMenuRequested SIGNAL so we
        # have to use events
        if not (e.type() == qt.QEvent.ContextMenu and isinstance(w, qt.QWorkspace)):
            return qt.QMainWindow.eventFilter(self, w, e)
        pos = e.globalPos()
        self.windowsMenu.popup(pos)
        return qt.QWorkspace.eventFilter(w, w, e)
