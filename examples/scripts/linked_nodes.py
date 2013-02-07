#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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

"This creates an HDF5 file that contains soft and external links"

import os

import tables as tb

output_dir = '../misc'
try:
    os.mkdir(output_dir)
except OSError:
    pass

# Open a new empty HDF5 file
hdf5_name = 'links_examples.h5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
fileh = tb.openFile(filepath_hdf5, mode = "w")

# Create some groups and add datasets to them
garrays = fileh.createGroup('/', 'arrays')
a1 = fileh.createCArray(garrays, 'a1', tb.Int64Atom(shape=(2,)), shape=(100, 3),
    title='A linked array')
gtables = fileh.createGroup('/', 'tables')
t1 = fileh.createTable(gtables, 't1',
    {'field1': tb.FloatCol(), 'field2': tb.IntCol()}, title='A linked table')

# Create a group and put some links there
glinks = fileh.createGroup('/', 'links')

# Hard link to table t1. If we remove t1 it will still be accessible via ht1.
# Hard links are not a subclass of tables.link.Link so they don't have a
# target attribute. Because hard links behave like regular nodes one can't
# infer if ht1 is a hard link by calling its __str__ method
ht1 = fileh.createHardLink(glinks, 'ht1', '/tables/t1')
t1.remove()

# Soft link to array a1
sa1 = fileh.createSoftLink(glinks, 'sa1', '/arrays/a1')

# Soft link to table t1. This is a dangling link because it points to a
# non-existing node. In order to get the pointed node the soft links are
# callable >>> psa1 = sa1()
st1 = fileh.createSoftLink(glinks, 'st1', '/tables/t1')
# Recreate the pointed table so the link is not dangling
hht1 = fileh.createHardLink(gtables, 't1', '/links/ht1')

# External links. They behave like soft links but point to nodes living in
# a different file
hdf5_name = 'external_file.h5'
filepath_hdf5 = os.path.join(output_dir, hdf5_name)
fileh2 = tb.openFile(filepath_hdf5, mode = "w")
new_a1 = a1.copy(fileh2.root, 'a1')
fileh2.close()
sa1.remove()
ea1 = fileh.createExternalLink(glinks, 'ea1', 'external_file.h5:/a1')

fileh.close()

