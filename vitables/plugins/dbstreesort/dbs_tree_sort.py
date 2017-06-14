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

"""Plugin that provides sorting algorithms for the DBs tree.

At the moment only two sorting algorithms are supported, alphabetical and
human (a.k.a. natural sorting). In order to obtain the default ViTables
random order of nodes just disable the plugin.

Once the plugin is enabled it works on any file opened after the enabling.
"""

__docformat__ = 'restructuredtext'
__version__ = '1.2'
plugin_name = 'Tree of DBs sorting'
comment = 'Sorts the display of the databases tree'

import logging
import os
import re
import vitables
from vitables.h5db import dbstreemodel
from vitables.h5db import groupnode
from vitables.h5db import leafnode
from vitables.h5db import linknode
from vitables.plugins.dbstreesort.aboutpage import AboutPage

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


translate = QtWidgets.QApplication.translate

log = logging.getLogger(__name__)


def customiseDBsTreeModel():
    """Slot connected to the convenience dbtree_model_created signal.
    """

    # The absolute path of the INI file
    ini_filename = os.path.join(os.path.dirname(__file__),
                                'sorting_algorithm.ini')
    config = configparser.ConfigParser()
    try:
        config.read(ini_filename)
        initial_sorting = config.get('DBsTreeSorting', 'algorithm')
    except (IOError, configparser.ParsingError):
        log.error(
            translate('DBsTreeSort', 'The configuration file of the '
                      'dbs_tree_sort plugin cannot be read.',
                      'DBsTreeSort error message'))
        return

    # The essence of the plugin is pretty simple, just monkeypatch
    # the insertRows() method of the model to get the desired result.
    # TODO how can the nodes be chronologically sorted?
    if initial_sorting == 'human':
        dbstreemodel.DBsTreeModel.insertRows = humanSort
    elif initial_sorting == 'alphabetical':
        dbstreemodel.DBsTreeModel.insertRows = alphabeticalSort
    else:
        log.warning(
            translate('DBsTreeSort', 'Unknown sorting algorithm: {}.',
                      'DBsTreeSort error message').format(initial_sorting))


def alphabeticalSort(self, position=0, count=1, parent=QtCore.QModelIndex()):
    """Sort nodes alphabetically.

    This method is called during nodes population and when files are
    opened/created.

    :Parameters:

     - `position`: the position of the first row being added.
     - `count`: the number of rows being added
     - `parent`: the index of the parent item.

     :Returns: True if the row is added. Otherwise it returns False.
     """

    # Add rows to the model and update its underlaying data store
    self.layoutAboutToBeChanged.emit()
    first = position
    last = position + count - 1
    self.beginInsertRows(parent, first, last)
    node = self.nodeFromIndex(parent)
    # Children are inserted at position 0, so inserted list must
    # be reversed if we want to preserve their original order
    for file_node in sorted(self.fdelta):
        self.root.insertChild(file_node, position)
    for name in sorted(self.gdelta, reverse=True):
        group = groupnode.GroupNode(self, node, name)
        node.insertChild(group, position)
    for name in sorted(self.ldelta, reverse=True):
        leaf = leafnode.LeafNode(self, node, name)
        node.insertChild(leaf, position)
    for name in sorted(self.links_delta, reverse=True):
        link = linknode.LinkNode(self, node, name)
        node.insertChild(link, position)
    self.dataChanged.emit(parent, parent)
    self.endInsertRows()
    self.layoutChanged.emit()

    # Report views about changes in data
    top_left = self.index(first, 0, parent)
    bottom_right = self.index(last, 0, parent)
    self.dataChanged.emit(top_left, bottom_right)

    return True


def alphanum_key(key):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    def convert(text): return int(text) if text.isdigit() else text

    return [convert(c) for c in re.split(r'(\d+)', key)]


def humanSort(self, position=0, count=1, parent=QtCore.QModelIndex()):
    """Sort nodes using a human sort algorithm.

    This method is called during nodes population and when files are
    opened/created.

    :Parameters:

    - `position`: the position of the first row being added.
    - `count`: the number of rows being added
    - `parent`: the index of the parent item.

    :Returns: True if the row is added. Otherwise it returns False.
    """

    # Add rows to the model and update its underlying data store
    self.layoutAboutToBeChanged.emit()
    first = position
    last = position + count - 1
    self.beginInsertRows(parent, first, last)
    node = self.nodeFromIndex(parent)
    # Children are inserted at position 0, so inserted list must
    # be reversed if we want to preserve their original order
    for file_node in sorted(self.fdelta):
        self.root.insertChild(file_node, position)
    for name in sorted(self.gdelta, reverse=True, key=alphanum_key):
        group = groupnode.GroupNode(self, node, name)
        node.insertChild(group, position)
    for name in sorted(self.ldelta, reverse=True, key=alphanum_key):
        leaf = leafnode.LeafNode(self, node, name)
        node.insertChild(leaf, position)
    for name in sorted(self.links_delta, reverse=True, key=alphanum_key):
        link = linknode.LinkNode(self, node, name)
        node.insertChild(link, position)
    self.dataChanged.emit(parent, parent)
    self.endInsertRows()
    self.layoutChanged.emit()

    # Report views about changes in data
    top_left = self.index(first, 0, parent)
    bottom_right = self.index(last, 0, parent)
    self.dataChanged.emit(top_left, bottom_right)

    return True


class DBsTreeSort(object):
    """Provides convenience methods and functions for sorting the tree of DBs.
    """

    UID = __name__
    NAME = plugin_name
    COMMENT = comment

    def __init__(self):
        """Class constructor.
        """

        self.vtapp = vitables.utils.getVTApp()
        self.vtapp.dbtree_model_created.connect(customiseDBsTreeModel)

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
                'about_text': translate(
                    'DBsTreeSortingPage',
                    '<qt><p>Plugin that provides sorting capabilities to '
                    'the tree of DBs.<p>For every open file, nodes (groups and'
                    ' leaves) are sorted when the file is open. '
                    'Nodes added at a later time are not sorted.<p>At the '
                    'moment only two sorting '
                    'algorithms are supported: human (a.k.a. natural sorting) '
                    'and alphabetical.</qt>',
                    'Text of an About plugin message box')}
        self.about_page = AboutPage(desc, parent)

        return self.about_page
