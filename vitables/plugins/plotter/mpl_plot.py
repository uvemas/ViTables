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

"""Plugin that provides very basic 2D plotting of datasets via matplotlib.

"""

__docformat__ = 'restructuredtext'
_context = 'Data2DPlotter'
__version__ = '0.1'
plugin_class = 'Data2DPlotter'

import sys, os, random

import tables

try:
    mpl_found = True
    import matplotlib
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
    from matplotlib.figure import Figure
except ImportError:
    mpl_found = False

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils


class Data2DPlotter(QMainWindow):
    """Embed matplotlib (mpl) plot in ViTables.
    """

    def __init__(self, parent=None):
        """ctor
        """

        if not mpl_found:
            return

        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Dataset 2D plotting')

        # Customise the Dataset Menu of ViTables main window
        self.vtapp = vitables.utils.getVTApp()
        self.addEntry()

        # Build the plugin main window
        self.icons_dictionary = self.setupIcons()
        self.gui_actions = self.setupActions()
        self.setupMenus()
        self.setupStatusBar()
        self.setupControls()

        # Flag to indicate if data have been loaded
        self.data_loaded = None


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


    def addEntry(self):
        """Add the Plot... entry to the Dataset menu.
        """

        menu = self.vtapp.dataset_menu

        # Create the action
        action = QAction(menu)
        action.setText(self.__tr("&Plot...", "Plot selected data"))
        action.setStatusTip(self.__tr("Plot the selected range of data via matplotlib", 
            "Status bar text for the Dataset -> Plot... action"))
        QObject.connect(action, SIGNAL("triggered()"), self.slotPlot)

        # Add the action to the Dataset menu
        menu.addAction(action)


    def slotFileSave(self):
        """Save the plot into a file.
        """

        file_choices = "PNG (*.png)|*.png"

        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)


    def slotHelpAbout(self):
        msg = """ A demo of using PyQt with matplotlib:

         * Use the matplotlib navigation bar
         * Add values to the text box and press Enter (or click "Draw")
         * Show or hide the grid
         * Drag the slider to modify the width of the bars
         * Save the plot to a file using the File menu
         * Click on a bar to receive an informative message
        """
        QMessageBox.about(self, "About this plugin", msg.strip())


    def on_pick(self, event):
        """Specialised handler for PickEvent events
        """

        # The event received here is of the type
        # matplotlib.backend_bases.PickEvent
        #
        # It carries lots of information, of which we're using
        # only a small amount here.
        # 
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on a point with coords:\n %s" % box_points
        QMessageBox.information(self, "Click!", msg)


    def setupStatusBar(self):
        """Initialise the status bar
        """

        status_bar = self.statusBar()
        self.status_text = QLabel(status_bar)
        self.status_text.setSizePolicy(QSizePolicy.MinimumExpanding, \
                                        QSizePolicy.Minimum)
        status_bar.addPermanentWidget(self.status_text)
        self.status_text.setToolTip(self.__tr(
            'The plot status',
            'The 2Dplotter plugin startup message'))
        status_bar.showMessage(self.__tr('Ready...',
            'The status bar startup message'))


    def setupIcons(self):
        """The icons used in the window's menus.
        """

        icons_path = 'vitables/plugins/plotter/icons/'
        icons = {}
        all = ('filesaveas', 'exit')
        for name in all:
            icons[name] = QIcon('%s%s.png' % (icons_path, name))

        return icons


    def setupActions(self):
        """Provide actions to the menubar and the toolbars.
        """

        actions = {}
        actions['fileSave'] = vitables.utils.createAction(self, 
            self.__tr('&Save', 'File -> Save'), QKeySequence('CTRL+S'), 
            self.slotFileSave, self.icons_dictionary['filesaveas'], 
            self.__tr('Save plot into a file', 
                'Status bar text for the File -> Save action'))

        actions['fileExit'] = vitables.utils.createAction(self, 
            self.__tr('E&xit', 'File -> Exit'), QKeySequence('CTRL+Q'), 
            self.close, self.icons_dictionary['exit'], 
            self.__tr('Quit DataPloter',
                'Status bar text for the File -> Exit action'))

        actions['helpAbout'] = vitables.utils.createAction(self, 
            self.__tr('&About', 'Help -> About'), None, 
            self.slotHelpAbout, None, 
            self.__tr('Display information about the  2DPlotter plugin',
                    'Status bar text for the Help -> About action'))
        return actions


    def setupMenus(self):

        """
        Set up the ploting window menus.

        Popus are made of actions, items and separators.
        """

        # Create the File menu and add actions/submenus/separators to it
        file_menu = self.menuBar().addMenu(self.__tr("&File", 
            'The File menu entry'))
        file_actions = ['fileSave', None, 'fileExit']
        vitables.utils.addActions(file_menu, file_actions, self.gui_actions)


        # Create the Help menu and add actions/submenus/separators to it
        help_menu = self.menuBar().addMenu(self.__tr("&Help", 
            'The Help menu entry'))
        help_actions = ['helpAbout']
        vitables.utils.addActions(help_menu, help_actions, self.gui_actions)


    def setupControls(self):
        """Configure GUI controls.
        """

        self.main_frame = QWidget()
        #
        # Matplotlib controls
        #

        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        # Since we have only one plot, we could use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111)

        # Bind the 'pick' event for clicking on one of the bars
        #
        self.canvas.mpl_connect('pick_event', self.on_pick)

        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        # PyQt4 controls
        # 
        self.draw_button = QPushButton("&Draw")
        self.connect(self.draw_button, SIGNAL('clicked()'), self.slotPlot)

        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), 
            self.slotUpdateGrid)

        slider_label = QLabel('Bar width (%):')
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(20)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.connect(self.slider, SIGNAL('valueChanged(int)'), self.slotPlot)

        #
        # Layout with box sizers
        # 
        hbox = QHBoxLayout()

        for w in [  self.draw_button, self.grid_cb,
                    slider_label, self.slider]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)


    def loadData(self):
        """Select a range of data and plot it.

        Currently this only works for PyTables arrays. The first two
        dimensions of the array are plotted.
        """

        # The dataset of the current leaf
        tree_index = self.vtapp.dbs_tree_view.currentIndex()
        tree_node = self.vtapp.dbs_tree_model.nodeFromIndex(tree_index)
        pytables_node = tree_node.node
        dataset = pytables_node.read()
        self.x = dataset[:, 0]
        self.y = dataset[:, 1]


    def slotPlot(self):
        """Basic plot with text labels.

        :Parameters:

        - x: tuple of values for the X coordinate
        - y: tuple of values for the Y coordinate
        """

        if self.data_loaded is None:
            self.loadData()
            self.data_loaded = True

        if len(self.x) == 0:
            self.x = arange(0, len(self.y))

        self.show()
        self.axes.plot(self.x, self.y, 'go')
        self.canvas.draw()


    def slotUpdateGrid(self):
        """Show/hide the grid
        """

        # Clear the axes and redraw the plot anew
        self.axes.clear()
        self.axes.grid(self.grid_cb.isChecked())
        self.slotPlot()
