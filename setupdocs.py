# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
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

"""
Create the Users Guide in both HTML and PDF formats.

distutils, sphinx and rst2pdf are required.
"""

import os
import shutil

from distutils.core import setup
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

from sphinx.setup_command import BuildDoc




class BuildSphinx(BuildDoc):
    """Customise the BuilDoc provided by the sphinx module setup_command.py
    """


    def run(self):
        """ Execute the build_sphinx command.

        The HTML and PDF docs will be included in the tarball. So this script
        MUST be executed before creating the distributable tarball via
        """

        # Build the Users Guide in HTML and TeX format
        for builder in ('html', 'pdf'):
            # Tidy up before every build
            try:
                os.remove(os.path.join(self.source_dir, 'index.rst'))
            except OSError:
                pass
            shutil.rmtree(self.doctree_dir, True)

            self.builder = builder
            self.builder_target_dir = os.path.join(self.build_dir, builder)
            self.mkpath(self.builder_target_dir)
            builder_index = 'index_{0}.txt'.format(builder)
            copy_file(os.path.join(self.source_dir, builder_index), 
                os.path.join(self.source_dir, 'index.rst'))
            BuildDoc.run(self)

        # Copy the docs to their final destination:
        # HTML docs (Users Guide and License) -> ./vitables/htmldocs
        # PDF guide -> ./doc
        output_dir = os.path.join("vitables", "htmldocs")
        if not os.access(output_dir, os.F_OK):
            # Include the HTML guide and the license in the package
            copy_tree(os.path.join(self.build_dir,"html"), output_dir)
            shutil.rmtree(os.path.join(output_dir,"_sources"))
            copy_file('LICENSE.html', output_dir)
        copy_file(os.path.join(self.build_dir, "pdf", 
            "UsersGuide.pdf"), "doc")

setup_args = {}

setup(cmdclass = {'build_sphinx': BuildSphinx},
    **setup_args
)

