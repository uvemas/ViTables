#!/usr/bin/env python3

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2024 Vicent Mas. All rights reserved
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
#       This script is based on a script by Ivan Vilata.

"""How to use the filenode module."""

import tables
from tables.nodes import filenode

h5file = tables.open_file('../misc/fnode.h5', 'w')
fnode = filenode.new_node(h5file, where='/', name='fnode_test')

counter = 0
while counter < 100000:
    line = f"This is a line inserted programmatically at position {counter}\n"
    fnode.write(line.encode("utf-8"))
    counter += 1

fnode.close()

node = h5file.root.fnode_test
fnode = filenode.open_node(node, 'a+')
fnode.write(bytearray("This is the last line.\n", "utf-8"))

fnode.attrs.content_type = 'text/plain; charset=us-ascii'

fnode.attrs.author = "Ivan Vilata i Balaguer"
fnode.attrs.creation_date = '2004-10-20T13:25:25+0200'
fnode.attrs.keywords_en = ["FileNode", "test", "metadata"]
fnode.attrs.keywords_ca = ["FileNode", "prova", "metadades"]
fnode.attrs.owner = 'ivan'
fnode.attrs.acl = {'ivan': 'rw', '@users': 'r'}

fnode.close()
h5file.close()
