# -*- coding: utf-8 -*-
#!/usr/bin/env python


########################################################################
#
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
#       $Id: nodeItemDelegate.py 1078 2008-10-23 11:11:55Z vmas $
#
########################################################################

"""
Here is defined the NodeItemDelegate class.

Classes:

* NodeItemDelegate(QtGui.QItemDelegate)

Methods:

* __init__(self, db_doc, nodepath)

Functions:

* __tr(source, comment=None)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import tables

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

import vitables.utils

class NodeItemDelegate(QtGui.QItemDelegate):
    """
    A custom delegate for editing items of the tree of databases model.

    The delegate is used for editing the text of items of the tree of
    databases model, i.e., the item's DisplayRole. In other words, it is
    used to edit the name of the nodes in a database object tree.
    """

    def __init__(self, parent=None):
        """
        Creates the custom delegate.
        """

        QtGui.QItemDelegate.__init__(self, parent)
        self.current_name = None
        self.vtapp = parent.vtapp


    def __tr(self, source, comment=None):
        """Translate function."""
        return unicode(QtGui.qApp.translate('NodeItemDelegate', source, comment))


    def setEditorData(self, editor, index):
        """
        Edits the data of an item with a given index.

        This method is automatically called when an editor is created,
        i.e., when the user double click an item.

        :Parameters:

        - `editor`: the editor widget
        - `index`: the index of the item being edited
        """

        node_name = index.model().data(index, QtCore.Qt.DisplayRole).toString()
        self.current_name = node_name
        editor.setText(node_name)


    def setModelData(self, editor, model, index):
        """
        Update the model with the just edited data.

        This method is called automatically when an editor is closed,
        i.e., when the user editing ends.

        :Parameters:

        - `editor`: the editor widget
        - `model`: the model whose data is being setup
        - `index`: the index of the item being edited
        """

        suggested_nodename = unicode(editor.text())

        node = model.nodeFromIndex(index)  # A GroupNode or a LeafNode instance
        parent = node.parent

        #
        # Check if the nodename is already in use
        #
        dst_dbdoc = model.getDBDoc(node.filepath)
        sibling = getattr(parent.node, '_v_children').keys()
        # Note that current nodename is not allowed as new nodename.
        # Embedding it in the pattern makes unnecessary to pass it to the
        # rename dialog via method argument and simplifies the code
        pattern = """(^%s$)|""" \
            """(^[a-zA-Z_]+[0-9a-zA-Z_ ]*)""" % unicode(self.current_name)
        info = [self.__tr('Renaming a node: name already in use', 
                'A dialog caption'), 
                self.__tr("""Source file: %s\nParent group: %s\n\nThere is """
                          """already a node named '%s' in that parent group.\n""", 
                          'A dialog label') % \
                    (parent.filepath, parent.nodepath, suggested_nodename)]
        # Validate the nodename
        nodename, overwrite = vitables.utils.getFinalName(suggested_nodename, sibling, 
            pattern, info)
        if nodename is None:
            editor.setText(self.current_name)
            return

        # Update the underlying data structure
        model.renameNode(index, nodename, overwrite)
        self.emit(QtCore.SIGNAL('closeEditor(QWidget *)'), editor)

        # Update the application status bar
        self.vtapp.updateStatusBar()
