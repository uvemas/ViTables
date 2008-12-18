# -*- coding: utf-8 -*-
#!/usr/bin/env python


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
#       $Id: dbDoc.py 1068 2008-10-11 17:15:42Z vmas $
#
########################################################################

"""
Here is defined the DBDoc class.

Classes:

* DBDoc(QtCore.QObject)

Methods:

* __init__(self, filepath, mode, tmp_dbdoc=None)
* __tr(self, source, comment=None)
* clearHiddenGroup(self)
* closeH5File(self)
* copyFile(self, dst_filepath)
* copyNode(self, nodepath)
* createGroup(self, where, final_name)
* cutNode(self, nodepath)
* deleteNode(self, nodepath)
* getFileFormat(self)
* getNode(self, where)
* listNodes(self)
* moveNode(self, src_h5file, childpath, dst_h5file, parentpath,
  childname=None)
* openH5File(self)
* pasteNode(self, parentpath)
* renameNode(self, nodepath, new_name)

Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import os

import tables
import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

import vitables.utils

class DBDoc(QtCore.QObject):
    """
    A database contained in an hdf5/PyTables file.

    This class exposes methods for reading/writing database nodes. It is
    a thin wrapper to the tables.File class
    """

    def __init__(self, filepath, mode, tmp_dbdoc=None):
        """
        Makes a data structure that defines a given database.

        A `DBDoc` instance is defined by the next attributes:

        - filepath
        - filename
        - mode
        - h5file, the File instance returned when filePath is opened

        :Parameters:

        - `filePath`: full path of the DB
        - `mode`: indicate the open mode of the database file. It
            can be 'r'ead-only or 'a'ppend
        - `tmp_dbdoc`: a reference to the temporary database DBDoc instance
        """

        QtCore.QObject.__init__(self)

        # The opening mode
        self.mode = mode

        # The full path of the database
        self.filepath = filepath

        # The filename of the database
        self.filename = os.path.basename(filepath)

        # The tables.File instance
        self.h5file = self.openH5File()

        # The temporary database. It is used as an intermediate storage
        # in copy and cut operations
        self.hidden_where = '/_p_cutNode'
        self.tmp_dbdoc = tmp_dbdoc
        if tmp_dbdoc != None:
            self.tmp_h5file = self.tmp_dbdoc.h5file
        else:
            self.tmp_dbdoc = self
            self.tmp_h5file = self.h5file


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate('DBDoc', source, comment))


    def openH5File(self):
        """Open the file tied to this instance."""

        h5file = None
        # If read-write access is required then test file writability
        if self.mode != 'r' and os.path.isfile(self.filepath):
            if not os.access(self.filepath, os.W_OK):
                self.mode = 'r'
                print self.__tr("""\nWarning: file access in read-write mode"""
                    """ is denied. It will be opened in read-only mode.""",
                    'A logger error message')

        try:
            h5file = tables.openFile(self.filepath, self.mode)
        except IOError, inst:
            print self.__tr("""\nError: %s.""",
                'A logger error message') % inst
        except:
            vitables.utils.formatExceptionInfo()
            print self.__tr("""Please, if you think this is a bug, report """
                """it to developers.""",
                'A logger error message')

        return h5file


    def closeH5File(self):
        """Closes a tables.File instance."""

        try:
            self.h5file.close()
        except:
            vitables.utils.formatExceptionInfo()


    def getFileFormat(self):
        """
        The format of the database file.

        This is an accessor method intended to be used by external
        classes.

        :Returns: the format of the database file
        """
        format = None
        if self.h5file:
            if self.h5file._isPTFile:
                format = 'PyTables file'
            else:
                format = 'Generic HDF5 file'

        return format


    def getNode(self, where):
        """
        The node whose path is where.

        :Parameter where: the full path of the retrieved node
        """

        try:
            node = self.h5file.getNode(where)
            return node
        except tables.exceptions.NoSuchNodeError:
            print self.__tr("""\nError: cannot open node %s in file %s """,
                'Error message') % (where, self.filepath)
            vitables.utils.formatExceptionInfo()
            return None


    def listNodes(self):
        """:Returns: the recursive list of full nodepaths for the file"""
        return [node._v_pathname for node in self.h5file.walkNodes('/')]


    # 
    # Editing databases
    # 

    def copyFile(self, dst_filepath):
        """
        Copy the contents of this file to another one.

        :Parameter dst_filepath: the full path of the destination file
        """

        """
        Remarks
        -------
        Given two open files in a ViTables session, overwriting one of them
        via File --> Save As... command may work or not. It depends on the
        operating system. On Unices it works because a process
        can delete or truncate a file open by a different process (unless
        file is blocked). On Windows it seems to work fine too.

        If the overwriting is not done via ViTables but in an interactive
        session it fails, due (probably) to HDF5 memory protection.
        """
        try:
            self.h5file.copyFile(dst_filepath, overwrite=True)
        except tables.exceptions.HDF5ExtError:
            print self.__tr("""\nError: unable to save the file %s as """\
                """%s. Beware that only closed files can be safely """\
                """overwritten via Save As...""",
                'A logger error message') % (self.filepath, dst_filepath)
            vitables.utils.formatExceptionInfo()


    def deleteNode(self, nodepath):
        """Delete a tables.Node.

        :Parameters:

        - `nodepath`: the full path of the node being deleted
        """

        try:
            self.h5file.removeNode(where=nodepath, recursive=True)
            self.h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()


    def clearHiddenGroup(self):
        """
        Clear the hidden group of the temporary database.

        Clear the contents of the hidden group before a new cut/copy is
        done. It means that at most one node will live in the hidden group
        at a given time.
        """

        # The hidden group of the temporary database
        hidden_group = self.tmp_h5file.getNode(self.hidden_where)
        # The list of copied/cut nodes paths
        children_dict = getattr(hidden_group, '_v_children')
        cut_nodes =  children_dict.keys()
        # Empty the hidden group
        for nodename in cut_nodes:
            cut_nodename = os.path.basename(nodename)
            self.tmp_h5file.removeNode(self.hidden_where,
                name=cut_nodename, recursive=True)
        self.tmp_h5file.flush()


    def cutNode(self, nodepath):
        """Moves a tables.Node to the hidden group of the temporary database.

        :Parameters:

        - `nodepath`: the full path of the node being copied
        """

        self.clearHiddenGroup()
        childname = os.path.basename(nodepath)
        self.moveNode(nodepath, self.tmp_dbdoc, self.hidden_where, childname)


    def pasteNode(self, src, parent, childname):
        """Copy a tables.Node to a different location.

        :Parameters:

        - `src`: the copied node being pasted
        - `parent`: the new parent of the node being pasted
        - `childname`: the new name of the node being pasted
        """

        try:
            self.h5file.copyNode(src.nodepath, newparent=parent.node,
                newname=childname, overwrite=True, recursive=True)
            self.h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()


    def renameNode(self, nodepath, new_name):
        """
        Rename the selected node from the object tree.

        :Parameters:

        - `nodepath`: the full path of the node being renamed
        - `new_name`: the node new name
        """

        h5file = self.h5file
        where, current_name = os.path.split(nodepath)

        try:
            h5file.renameNode(where, new_name, current_name, overwrite=1)
            h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()


    def createGroup(self, where, final_name):
        """
        Create a new group under the given location.

        :Parameters:

        - `where`: the full path of the parent node
        - `final_name`: the new group name
        """

        h5file = self.h5file
        try:
            if final_name in h5file.getNode(where)._v_children.keys():
                h5file.removeNode(where, final_name, recursive=True)
            h5file.createGroup(where, final_name, title='')
            h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()


    def moveNode(self, childpath, dst_dbdoc, parentpath, childname):
        """Move a tables.Node to a different location.

        :Parameters:

        - `childpath`: the full path of the node being moved
        - `dst_dbdoc`: the destination database (a DBDoc instance)
        - `parentpath`: the full path of the new parent node
        - `childname`: the name of the node in its final location
        """

        try:
            dst_h5file = dst_dbdoc.h5file
            parent_node = dst_h5file.getNode(parentpath)
            if self.h5file is dst_h5file:
                self.h5file.moveNode(childpath, newparent=parent_node,
                    newname=childname, overwrite=True)
            else:
                self.h5file.copyNode(childpath, newparent=parent_node,
                    newname=childname, overwrite=True, recursive=True)
                dst_h5file.flush()
                src_where, src_nodename = os.path.split(childpath)
                self.h5file.removeNode(src_where, src_nodename, recursive=1)
            self.h5file.flush()
        except:
            vitables.utils.formatExceptionInfo()


