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
#       $Id: dbDoc.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the DBDoc class.

Classes:

* DBDoc(qt.QObject)

Methods:

* __init__(self, filepath, mode)
* __tr(self, source, comment=None)
* openH5File(self)
* closeH5File(self)
* getFileFormat(self)
* getFileName(self)
* getFileMode(self)
* getH5File(self)
* getNode(self, where)
* listNodes(self)
* copyFile(self, dst_filepath)
* createGroup(self, where, final_name)
* cut(self, where, name, target_node)
* copyNode(self, src_dbdoc, src_nodepath, target_dbdoc, parentpath, final_name)
* move(self, src_nodepath, target_dbdoc, target_parentpath, final_name)
* rename(self, where, final_name, current_name)
* delete(self, where, name, is_visible=True)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import os

import tables
import qt

import vitables.utils

class DBDoc(qt.QObject):
    """
    A database contained in an h5 file.

    This class represents a database (model) that is controlled by the
    database manager (controller).
    It exposes methods to get some database properties.
    """


    def __init__(self, filepath, mode):
        """
        Makes a data structure that defines a given database.

        A `DBDoc` instance is defined by the next attributes:

        - filepath
        - filename
        - mode
        - h5_file, the File instance returned when filePath is opened

        :Parameters:

        - `filePath`: full path of the DB
        - `mode`: indicate the open mode of the database file. It
            can be 'r'ead-only or 'a'ppend
        """

        qt.QObject.__init__(self)

        # The attached view
        self.dbview = None

        # The opening mode
        self.mode = mode

        # The full path of the database
        self.filepath = filepath

        # The filename of the database
        self.filename = os.path.basename(filepath)

        # The tables.File instance
        # Value used if an error occurs
        self.h5_file = self.openH5File()

        # The file format
        self.file_format = self.getFileFormat()

    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('DBDoc', source, comment).latin1()


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
            self.h5_file.close()
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
        if self.h5_file and self.h5_file._isPTFile:
            format = 'PyTables file'
        else:
            format = 'Generic HDF5 file'

        return format


    def getFileName(self):
        """:Returns: the filename of the open file"""
        return self.filename


    def getFileMode(self):
        """:Returns: the access mode of the open file"""
        return self.mode


    def getH5File(self):
        """:Returns: a tables.File instance"""
        return self.h5_file


    def getNode(self, where):
        """
        The node whose path is where.

        :Parameter where: the full path of the retrieved node
        """

        try:
            node = self.h5_file.getNode(where)
            return node
        except tables.exceptions.NoSuchNodeError:
            print self.__tr("""\nError: cannot open node %s in file %s """,
                'Error message') % (where, self.filepath)
            vitables.utils.formatExceptionInfo()
            return None



    def listNodes(self):
        """:Returns: the recursive list of full nodepaths for the file"""
        return [node._v_pathname for node in self.h5_file.walkNodes('/')]


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
            self.getH5File().copyFile(dst_filepath, overwrite=True)
        except tables.exceptions.HDF5ExtError:
            print self.__tr("""\nError: unable to save the file %s as """\
                """%s. Beware that only closed files can be safely """\
                """overwritten via Save As...""",
                'A logger error message') % (self.filepath, dst_filepath)
            vitables.utils.formatExceptionInfo()


    def createGroup(self, where, final_name):
        """
        Create a new group under the given location.

        :Parameters:

        - `where`: the full path of the parent node
        - `final_name`: the new group name
        """

        creation_ok = False
        h5file = self.getH5File()
        try:
            if final_name in h5file.getNode(where)._v_children.keys():
                h5file.removeNode(where, final_name, recursive=True)
            h5file.createGroup(where, final_name, title='')
            h5file.flush()
            creation_ok = True
        except:
            vitables.utils.formatExceptionInfo()
        # Update the database view
        if creation_ok:
            self.dbview.createGroup(where, final_name)


    def cut(self, where, name, target_node):
        """
        Cut the selected node from the object tree.

        The cut node is moved to the hidden group ``_p_cutNode``, in the
        temporary database.

        :Parameters:

        - `where`: the full path of the parent node
        - `name`: the cut node name
        - `target_node`: the hidden group where the cut node will be
        stored
        """

        cut_ok = False
        try:
            # tables.File.moveNode() method cannot move nodes between
            # different files so, a workaround is needed here
            h5file = self.getH5File()
            h5file.copyNode(where=where, name=name, newparent=target_node,
                overwrite=True, recursive=True)
            h5file.removeNode(where, name, recursive=True)
            h5file.flush()
            target_node._v_file.flush()
            cut_ok = True
        except:
            vitables.utils.formatExceptionInfo()
        # Propagate changes to the attached view
        if cut_ok:
            self.dbview.delete(where, name)


    def copyNode(self, src_dbdoc, src_nodepath, target_dbdoc, parentpath,
        final_name):
        """
        Paste a copied/cut node under the selected group.

        :Parameters:

        - `src_dbdoc`: the database where the node being pasted lives
        - `src_nodepath`: the full path in the source database of the
            node being pasted
        - `target_dbdoc`: the database where the node being pasted will live
        - `parentpath`: the path of the target group
        - `final_name`: the wanted name for the node being pasted
        """

        paste_ok = False
        try:
            parent_node = target_dbdoc.getNode(parentpath)
            h5file = self.getH5File()
            h5file.copyNode(src_nodepath, newparent=parent_node,
                newname=final_name, overwrite=True, recursive=True)
            parent_node._v_file.flush()
            paste_ok = True
        except:
            vitables.utils.formatExceptionInfo()
        # Propagate changes to the attached view
        if paste_ok:
            self.dbview.copyNode(self.filepath, src_nodepath,
                target_dbdoc.filepath, parentpath, final_name)


    def move(self, src_nodepath, target_dbdoc, target_parentpath, final_name):
        """
        Move the selected node to another location.

        :Parameters:

        - `src_nodepath`: the full path in the source database of the
            node being dropped
        - `target_dbdoc`: the database where the node being dropped will live
        - `target_parentpath`: the path of the new parent group of the
            node being dropped
        - `final_name`: the name of the pasted node in the target file
        stored
        """

        move_ok = False
        try:
            parent_node = target_dbdoc.getNode(target_parentpath)
            h5file = self.getH5File()
            # If the node is being moved to a different location in the
            # same database
            if self == target_dbdoc:
                h5file.moveNode(src_nodepath, newparent=parent_node,
                    newname=final_name, overwrite=True)
            # If the node is being moved to a different database
            else:
                h5file.copyNode(src_nodepath, newparent=parent_node,
                    newname=final_name, overwrite=True, recursive=True)
                parent_node._v_file.flush()
                src_where, src_nodename = os.path.split(src_nodepath)
                h5file.removeNode(src_where, src_nodename, recursive=1)
            h5file.flush()
            move_ok = True
        except:
            vitables.utils.formatExceptionInfo()
        # Propagate changes to the attached view
        if move_ok:
            self.dbview.move(self.filepath, src_nodepath, target_dbdoc.filepath,
                target_parentpath, final_name)


    def rename(self, where, final_name, current_name):
        """
        Rename the selected node from the object tree.

        :Parameters:

        - `where`: the full path of the parent node
        - `final_name`: the node new name
        - `current_name`: the node current name
        """

        renaming_ok = False
        h5file = self.getH5File()

        try:
            h5file.renameNode(where, final_name, current_name,  overwrite=1)
            h5file.flush()
            renaming_ok = True
        except:
            vitables.utils.formatExceptionInfo()
        # Propagate changes to the attached view
        if renaming_ok:
            self.dbview.renameSelected(where, final_name, current_name)


    def delete(self, where, name, is_visible=True):
        """
        Delete the selected item from the object tree.

        For groups the deletion is made recursively.
        Cut nodes live in a hidden group of the temporary database so
        they are not visible in the tree view and don't have to be deleted
        from there.

        :Parameters:

        - `where`: the path of the parent of the node being deleted
        - `name`: the name of the node being deleted
        - `is_cut_node`: indicates if the node being deleted is a cut one
        """

        deleting_ok = False
        h5file = self.getH5File()

        try:
            h5file.removeNode(where, name, recursive=1)
            h5file.flush()
            deleting_ok = True
        except:
            vitables.utils.formatExceptionInfo()
        # Propagate changes to the attached view
        # Cut nodes are not visible in the tree view so they don't have
        # be deleted from there
        if deleting_ok and is_visible:
            self.dbview.delete(where, name)
