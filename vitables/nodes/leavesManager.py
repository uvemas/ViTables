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
#       $Id: leavesManager.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the LeavesManager class.

Classes:

* LeavesManager(qt.QObject)

Methods:

* __init__(self, vtapp)
* __tr(self, source, comment=None)
* createViewAndTrack(self, document, lvitem)
* createLeafDoc(self, dbdoc, nodepath)
* createLeafView(self, document, lvitem)
* closeView(self, key)
* closeLeaf(self, target)
* getLeafDoc(self, lvitem)
* getLeafView(self, filepath, nodepath)
* viewList(self)
* cleanLeavesUnderKey(self, node_key)
* slotNodeProperties(self, dbdoc, current)
* getNodeInfo(self, dbdoc, lvitem)
* slotUnImplementedMsg(self)
* move(self, initial_nodepath, final_nodepath, src_filepath, target_dbdoc)
* rename(self, filepath, final_path, initial_path)
* queryTable(self, leafdoc, tmp_h5file)
* getQueryInfo(self)
* enterQuery(self, info, query_info, initial_query, src_table)
* eventFilter(self, receiver, event)

Functions:

* setInfoDictionary(source_table)
* setSearchableFields(source_table, info)
* setInitialCondition(last_query_info, info)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sets

import tables
import qt

import vitables.utils
from vitables.vtTables import hpTable
from vitables.vtWidgets import queryDlg
from vitables.nodes.leafView import LeafView
from vitables.nodes.groupDoc import GroupDoc
from vitables.nodes.tableDoc import TableDoc
from vitables.nodes.arrayDoc import ArrayDoc
from vitables.nodes.unimplementedDoc import UnImplementedDoc
from vitables.nodeProperties import nodePropDlg

def setInfoDictionary(source_table):
    """
    Set a dictionary with information about the table being queried.
    
    :Parameter source_table:
        the instance of `tables.Table` being queried
    """

    # TABLE INFORMATION
    info = {}
    info['nrows'] = source_table.nrows
    info['src_filepath'] = source_table._v_file.filename
    info['src_path'] = source_table._v_pathname
    info['name'] = source_table._v_name
    # Fields info: top level fields names, flat fields shapes and types
    info['col_names'] = sets.Set(source_table.colnames)
    info['col_shapes'] = \
        dict((k, v.shape) for (k, v) in source_table.coldescrs.iteritems())
    info['col_types'] = source_table.coltypes
    # Fields that can be queried
    info['condvars'] = {}
    info['valid_fields'] = []
    return info


def setSearchableFields(source_table, info):
    """
    Set the searchable fields and condition variables.
    
    Valid fields are those that fullfill the following `dtype`, `shape`,
    and `name` restrictions:

    - `dtype` cannot be complex
    - `shape` must be ()
    - `name` cannot contain blanks
    
    :Parameters:

    - `source_table`: the table being queried
    - `info`: a dictionary with information about the table being queried
    """

    # First discard nested fields
    valid_fields = \
    info['col_names'].intersection(info['col_shapes'].keys())

    # Then discard fields that aren't scalar and those that are complex
    for name in valid_fields.copy():
        if (info['col_shapes'][name] != ()) or \
        info['col_types'][name].count('complex'):
            valid_fields.remove(name)

    # Among the remaining fields, those whose names contain blanks
    # cannot be used in conditions unless they are mapped to
    # variables with valid names
    index = 0
    for name in valid_fields.copy():
        if name.count(' '):
            while ('col%s' % index) in valid_fields:
                index = index + 1
            info['condvars']['col%s' % index] = \
                source_table.cols._f_col(name)
            valid_fields.remove(name)
            valid_fields.add('col%s (%s)' % (index, name))
            index = index + 1
    info['valid_fields'] = valid_fields


def setInitialCondition(last_query_info, info):
    """
    Set the initial condition of the query.

    :Parameters:

    - `last_query_info`: a tuple with the string components of the last query
    - `info`: a dictionary with information regarding the query
    """

    if (last_query_info[0], last_query_info[1]) == \
    (info['src_filepath'], info['src_path']):
        initial_condition = last_query_info[2]
    else:
        initial_condition = ''
    return initial_condition


class LeavesManager(qt.QObject):
    """
    Manages the creation/deletion of leaves in the workspace. It
    manages also the creation/deletion of `Properties` dialogs.
    As the other managers, this one is created at application init
    time.
    This class controls models (it is a controller component of the
    application), models being tree open nodes. In particular it is
    intended to:

    - create models (`NodeDoc` instances)
    - bind every created model to a unique view (`LeafView` instance)
    - destroy models when its binded view is destroyed
    - keep track of existing models
    """


    def __init__(self, vtapp):
        """:Parameter vtapp: a `VTApp` instance"""

        qt.QObject.__init__(self)

        # The application GUI
        self.gui = vtapp.gui

        # Mapping that will track existent documents and filters. Items
        # have the format (dbFullPath:leafFullPath, [document, view])
        self._openLeaf = {}
        self.last_creation_key = ''

        # Size criterium for datasets. If a document has more than maxRows rows
        # it is considered large, if not it is considered small.
        self.max_rows = 1000

        # Querying tables related variables
        self.counter = 0
        self.ft_names = []
        self.last_query_info = ['', '', '']
        self.query_info = {}


    #
    # methods for leafdoc/leafview creation and deletion #####################
    #

    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('LeavesManager', source, comment).latin1()


    def createViewAndTrack(self, document, lvitem):
        """
        Tracks a document and ties it to a view.

        - a (document, view) pair is created
        - the tracking system is updated with the new pair (if any)
        - the node view is displayed

        :Parameters:

        - `document`: the `NodeDoc` instance being opened
        - `lvitem`: the tree view lvitem being opened
        """

        # Attach a view to the model
        view = self.createLeafView(document, lvitem)
        document.leafview = view
        # Track the model and view pair.
        # WARNING! This must be done before the view is shown because
        # showing the view calls the VTApp.slotUpdateActions
        # (via WindowsActivated SIGNAL) which, in turn, read the
        # tracking dictionary
        self._openLeaf[self.last_creation_key] = (document, view)
        view.hp_table.show()


    def createLeafDoc(self, dbdoc, nodepath):
        """
        Creates a leafdoc for a given object tree leaf.

        If the leafdoc already exists its view is raised.
        If the leafdoc doesn't exist it is created.

        :Parameters:

        - `dbdoc`: the database where the dataset will be read
        - `nodepath`: the path of the dataset being read
        """

        # The key of the node in the tracking leaves dictionary
        self.last_creation_key = '%s#@#%s' % (dbdoc.filepath, nodepath)

        # Creates the leafdoc
        # The node mapped to the selected item
        node = dbdoc.getNode(nodepath)
        if isinstance(node, tables.Group):
            leafdoc = GroupDoc(dbdoc, nodepath)
        elif isinstance(node, tables.Table):
            leafdoc = TableDoc(dbdoc, nodepath)
        elif isinstance(node, tables.Array) or \
            isinstance(node, tables.CArray) or \
            isinstance(node, tables.EArray) or \
            isinstance(node, tables.VLArray):
            leafdoc = ArrayDoc(dbdoc, nodepath)
        elif isinstance(node, tables.UnImplemented):
            # PyTables cannot open the leaf
            leafdoc =  UnImplementedDoc(dbdoc, nodepath)
        return leafdoc


    def createLeafView(self, document, lvitem):
        """
        Create a tabular leafview for a given document.

        Small documents (those with less than 1000 rows) are displayed with
        regular tables. Large documents (those with at least 1000 rows) are
        displayed with customized tables that have been designed specially
        to show large datasets.

        :Parameters:

        - `document`: the document being displayed
        - `lvitem`: the object tree node being opened
        """

        # Large datasets are displayed in a table with a constant number of rows
        nrows = min(self.max_rows, document.numRows())
        ncolumns = document.numCols()

        leafview = LeafView(lvitem, self.max_rows, document, nrows, ncolumns,
            self.gui.workspace)
        # Install the event filter in the leafview
        leafview.hp_table.installEventFilter(self)

        # Connect signals to slots
        self.connect(leafview,
            qt.PYSIGNAL('infoButtonClicked(DBDoc, TreeNode)'),
            self.slotNodeProperties)

        return leafview


    def closeView(self, key):
        """
        Closes a leafview (array or table).

        The method is called when the leafview is closed via `Node -->
        Close`.
        In this case the close procedure is done in three steps:

        - get the leafview to be closed
        - close the leafview. It raises a close event.
        - the event filter catches the close event and processes it via
            `closeLeaf` method. It updates the tracking dictionary

        :Parameter key: the key of the leafview being closed.
        """

        leafview = self._openLeaf[key][1]
        # The event filter will catch and process this close event
        leafview.hp_table.close()


    def closeLeaf(self, target):
        """
        Closes a leaf (array or table).

        The method is called when the event filter catches a close
        event. It can occurs in two different ways: when the view
        is closed by clicking the close button of the title bar or
        as a final step when the view is closed via `Node --> Close View`.
        It deletes the pair `(NodeDoc, LeafView)` mapped to the selected
        tree leafview item, and updates the leaves manager tracking system.

        :Parameter target: the `HPTable` instance being closed
        """

        # Update the tracking system and let the event filter to close the
        # view
        key = '%s#@#%s' % (target.doc.filepath, target.doc.nodepath)
        del  self._openLeaf[key], target

    #
    # accessor methods ###################################
    #

    def getLeafDoc(self, lvitem):
        """
        Gets the leaf document mapped to a given tree view item.

        This is a getter method that allows to external classes to inspect
        the tracking dictionary without breaking its privacity.

        :Parameter current: the tree view item mapped to the doc being obtained

        :Returns:
            the `NodeDoc` instance mapped to the pair `(filePath, nodePath)`
        """

        key = '%s#@#%s' % (lvitem.getFilepath(), lvitem.where)
        if self._openLeaf.has_key(key):
            return self._openLeaf[key][0]
        else:
            return None


    def getLeafView(self, filepath, nodepath):
        """
        Gets the leaf view defined by the pair filepath, nodepath.

        This is a getter method that allows to external classes to inspect
        the tracking dictionary without breaking its privacity.

        :Parameters:

        - `filepath`: the full path of the database file
        - `nodepath`: the full path of the leaf

        :Returns:
            the `LeafView` instance mapped to the pair `(filepath, nodepath)`
        """

        key = '%s#@#%s' % (filepath, nodepath)
        if self._openLeaf.has_key(key):
            return self._openLeaf[key][1]
        else:
            return None

    #
    # helper methods ###################################
    #

    def viewList(self):
        """
        The list of currently open views.

        This list is used to save the session state at quiting time.
        List items have the format ``filePath#@#nodePath``

        :Returns: the list of currently open files and views
        """
        return [key for key in self._openLeaf.keys()]


    def cleanLeavesUnderKey(self, node_key):
        """
        Wipe overwritten leaves off the workspace.

        Editing nodes requires to close views in the following cases:

        - V is being cut
        - V is being overwritten during a paste operation
        - V is being overwritten during a drop operation
        - V is being overwritten during a rename operation
        - V is being deleted

        where V is the node (or some of its ancestors) attached to the
        view being closed.

        :Parameter node_key: the node key in the tracking dictionary
        """

        # Check for root node
        filepath, nodepath = node_key.split('#@#')
        if nodepath == '/':
            node_key = node_key[0:-1]

        # provided that nodepath is /path/to/node then
        # if /path/to/node is a leaf and has a view it will be closed
        # if /path/to/node/child is a leaf and has a view it will be closed
        # if /path/to/node2 is a leaf and has a view it will *not* be closed
        # (which is correct. This is why we use %s/ instead of just %s)
        for key in self.viewList():
            if key.count('%s/' % node_key) or (key == node_key):
                self.closeView(key)


    #
    # methods for getting info about leaves ###################################
    #


    def slotNodeProperties(self, dbdoc, current):
        """
        Display the properties dialog of a given node.

        The method is called by clicking the info button of any open node
        view or by selecting a tree view item and launching the command
        `Node --> Properties`.

        :Parameters:

        - `dbdoc`: the `DBDoc` instance where the reported node lives
        - `current`: the tree view item being reported
        """

        info = self.getNodeInfo(dbdoc, current)
        if info['type'] == 'UnImplemented':
            self.slotUnImplementedMsg()
        else:
            nodePropDlg.NodePropDlg(info, dbdoc.mode)


    def getNodeInfo(self, dbdoc, lvitem):
        """
        Gets info about the selected node.

        This method opens a tree view item for inspecting. A new document
        is created, inspected and, eventually, deleted, but not tracked.
        Obtained info includes name, path, type of node, number of childs,
        and info about the real data that are contained in the node.

        :Parameters:

        - `dbdoc`: the `DBDoc` instance where the inspected node lives
        - `lvitem`: the selected tree view item
        """

        # If the doc doesn't exist it is created (not tracked and with no view)
        leafdoc = self.getLeafDoc(lvitem) or self.createLeafDoc(dbdoc,
            lvitem.where)
        return leafdoc.getNodeInfo()


    def slotUnImplementedMsg(self):
        """Show a message box about UnImplemented objects."""

        # Display a customized About dialog
        about = qt.QMessageBox(
            self.__tr('About UnImplemented nodes', 'A dialog caption'),
            self.__tr(
            """Actual data for this node are not accesible.<br> """
            """The combination of datatypes and/or dataspaces in this node"""
            """ is not yet supported by PyTables.<br>"""
            """If you want to see this kind of dataset implemented in """
            """PyTables, please, contact the developers.""",
            'Text of the Unimplemented node dialog'),
            qt.QMessageBox.Information, qt.QMessageBox.NoButton,
            qt.QMessageBox.NoButton, qt.QMessageBox.NoButton, self.gui)

        # Show the message
        about.show()

    #
    # Editing leaves
    #

    def move(self, initial_nodepath, final_nodepath, src_filepath, target_dbdoc):
        """
        Propagate moving changes from the object tree to dataset views.

        This method is called when a node is moved in the tree view.

        :Parameters:

        - `initial_nodepath`: the path of the node before moving it
        - `final_nodepath`: the path of the node after moving it
        - `src_filepath`: the filepath of the source database
        - `target_dbdoc`: the target database
        """

        src_key = '%s#@#%s' % (src_filepath, initial_nodepath)
        for key in self.viewList():
            # Note that key looks like filepath#@#leaf_path but node_key
            # looks like filepath#@#node_path (where node can be group or leaf)
            if key.count('%s/' % src_key) or (key == src_key):
                old_nodepath = key.split('#@#')[-1]
                new_nodepath = old_nodepath.replace(initial_nodepath,
                    final_nodepath, 1)
                # Create a new leafdoc
                leafdoc = self.createLeafDoc(target_dbdoc, new_nodepath)
                # The new leafdoc reuses the existing leafview
                leafview = self._openLeaf[key][1]
                leafview.doc = leafdoc
                leafdoc.leafview = leafview
                # Update the reused leafview
                leafdoc.move()
                # Update the open leaves tracking dictionary
                del self._openLeaf[key]
                self._openLeaf['%s#@#%s' % (target_dbdoc.filepath,
                    leafdoc.nodepath)] = (leafdoc, leafdoc.leafview)


    def rename(self, filepath, final_path, initial_path):
        """
        Propagate renaming changes from the object tree to dataset views.

        This method is called when a node is renamed in the tree view.

        :Parameters:

        - `filepath`: the path of the just changed database
        - `initial_path`: the path of the node before the change
        - `final_path`: the path of the node after the change
        - `overwrite`: indicates if the renaming will overwrite some node
        """

        node_key = '%s#@#%s' % (filepath, initial_path)
        for key in self.viewList():
            # Note that key looks like filepath#@#leaf_path but node_key
            # looks like filepath#@#node_path (where node can be group or leaf)
            if key.count('%s/' % node_key) or (key == node_key):
                nodedoc = self._openLeaf[key][0]
                nodedoc.rename(final_path, initial_path)
                # Update the open leaves tracking dictionary
                del self._openLeaf[key]
                self._openLeaf['%s#@#%s' % (filepath, nodedoc.nodepath)] = \
                    (nodedoc, nodedoc.leafview)

    #
    # Querying tables
    #
    
    def queryTable(self, leafdoc, tmp_h5file):
        """
        Add a new filtered table to the temporary database.

        :Parameters:

        - `leafdoc`: the `LeafDoc` instance being queried
        - `tmp_h5file`:
            the `tables.File` instance tied tho the temporary database
        """

        result = (None, None)
        source_table = leafdoc.node
        if source_table.nrows <= 0:
            print self.__tr("""Caveat: dataset is empty. Nothing to query.""",
                'Warning message for users')
            return result

        # TABLE INFORMATION
        info = setInfoDictionary(source_table)

        # FIELDS SELECTION
        setSearchableFields(source_table, info)

        # If table has not columns suitable to be filtered does nothing
        if not info['valid_fields']:
            print self.__tr("""\nError: the selected table has no """
            """columns suitable to be queried. All columns are nested, """
            """multidimensional or have a Complex data type.""",
            'An error when trying to query a table')
            return result
        elif len(info['valid_fields']) != len(info['col_names']):
        # Log a message if non selectable fields exist
            print self.__tr("""\nWarning: some table columns contain """
               """nested, multidimensional or Complex data. They """
               """cannot be queried so are not included in the Column"""
               """ selector of the query dialog.""",
               'An informational note for users')

        # THE INITIAL CONDITION FOR THE QUERY DIALOG
        initial_condition = setInitialCondition(self.last_query_info, info)

        # GET THE QUERY COMPONENTS
        self.enterQuery(info, self.query_info, initial_condition, leafdoc.node)
        self.query_info['condvars'] = info['condvars']
        if not self.query_info['condition']:
            return result

        # SET THE TITLE OF THE RESULT TABLE
        title = self.query_info['condition']
        for name in info['valid_fields']:
            # Valid fields can have the format 'fieldname' or 
            # 'varname (name with blanks)' so a single blank shouldn't
            # be used as separator
            components = name.split(' (')
            if len(components) > 1:
                fieldname = '(%s' % components[-1]
                title = title.replace(components[0], fieldname)

        # QUERY THE TABLE
        qt.qApp.setOverrideCursor(qt.QCursor(qt.Qt.WaitCursor))
        try:
            # Query the table
            selected_rows = leafdoc.queryTable(tmp_h5file, self.query_info, title)
            # Update the list of names in use for filtered tables
            self.ft_names.append(self.query_info['ft_name'])
            self.last_query_info = [info['src_filepath'], info['src_path'],
                self.query_info['condition']]
            result = (self.query_info['ft_name'], selected_rows)
        finally:
            qt.qApp.restoreOverrideCursor()

        # RETURN THE RESULT
        return result


    def getQueryInfo(self):
        """
        Get the info regarding the query being done.

        This method is implemented mainly for testing purposes.
        """
        return self.query_info


    def enterQuery(self, info, query_info, initial_query, src_table):
        """
        Raise a New filter dialog.

        The user defines the query to be done in this dialog: name of the
        result table, retrieve indices, condition and range of rows to be
        queried.

        :Parameters:

        - `info`: a dictionary with information about the table being queried
        - `query_info`: a dictionary with information about the query itself
        - `initial_query`: the dialog will be setup with this query (if any)
        - `src_table`: the tables.Table instance being queried
        """

        # Update the sufix of the suggested name to ensure that it is not in use
        self.counter = self.counter + 1
        # Retrieve information about the query: condition to
        # be applied, involved range of rows, name of the
        # filtered table and name of the column of returned indices
        query = queryDlg.QueryDlg(query_info, info, self.ft_names, 
            self.counter, initial_query, src_table)
        try:
            query.exec_loop()
            # Cancel clicked
            if query.result() == qt.QDialog.Rejected:
                self.counter = self.counter - 1 # Restore the counter value
        finally:
            del query
        return query_info


    def eventFilter(self, receiver, event):
        """
        Handle close and focus in events.

        When the close button of a view is clicked some
        tidy up must be done before to close it (mainly update the
        tracking dictionary).
        By filtering close events of the views, its close behavior
        can be customised to fit our needs.

        :Parameters:

        - `receiver`: the object that receives the event
        - `event`: the received event
        """

        if isinstance(receiver, hpTable.HPTable):
            if event.type() == qt.QEvent.FocusIn:
                # Ensure that the clicked window looks like the active window
                self.gui.workspace.emit(qt.SIGNAL('windowActivated(QWidget *)'), (receiver, ))
                return qt.QWidget.eventFilter(self, receiver, event)
            elif event.type() == qt.QEvent.Close:
                self.closeLeaf(receiver)
                return False
            else:
                return qt.QWidget.eventFilter(self, receiver, event)
        return qt.QWidget.eventFilter(self, receiver, event)
