# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2011 Vicent Mas. All rights reserved
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
Setup script for the vitables package.
"""

import sys
import os
import shutil
import glob

from distutils.core import setup
from distutils.spawn import find_executable
from distutils.spawn import spawn
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

try:
    from sphinx.setup_command import BuildDoc
except ImportError:
    pass


sphinx_found = True



if sphinx_found:
    class BuildSphinx(BuildDoc):
        """Customise the BuilDoc provided by the sphinx module setup_command.py
        """


        def run(self):

            """ Execute the build_sphinx command.

            The HTML and PDF docs are included in the tarball. So even if 
            sphinx or pdflatex are not installed on the user's system she will 
            get the full documentation installed when installing ViTables in 
            the usual way::

                # python setup.py install

            because the build_sphinx command will not be executed by default.

            If user is installing from a binary package (which will not include
            the docs, I think), in order to ensure that she will always end up with
            the docs being installed, the package should depend on the sphinx and
            pdflatex packages and the `sphinx_found` variable should be set to 
            True.
            """

            # Build the Users Guide in HTML and TeX format
            for builder in ('html', 'latex'):
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

            # Build the Users Guide in PDF format
            builder_latex_dir = os.path.join(self.build_dir, 'latex')
            make_path = find_executable("make")
            spawn([make_path, "-C", builder_latex_dir, "all-pdf"])

            # Copy the docs to their final destination:
            # HTML docs (Users Guide and License) -> ./vitables/htmldocs
            # PDF guide -> ./doc
            output_dir = os.path.join("vitables", "htmldocs")
            if not os.access(output_dir, os.F_OK):
                # Include the HTML guide and the license in the package
                copy_tree(os.path.join(self.build_dir,"html"), output_dir)
                shutil.rmtree(os.path.join(output_dir,"_sources"))
                copy_file('LICENSE.html', output_dir)
            copy_file(os.path.join(builder_latex_dir, 
                "UsersGuide.pdf"), "doc")

use_py2app = False
if sys.platform == 'darwin' and 'py2app' in sys.argv:
    import py2app
    use_py2app = True

setup_args = {}
if use_py2app:
    setup_args['app'] = ['macosxapp/vitables-app.py']
    setup_args['options'] = dict(
        py2app=dict(
            argv_emulation=True,
            iconfile='macosxapp/ViTables.icns', 
            # Do not include system or vendor Python.
            semi_standalone=True, 
            # Use system PyTables and NumPy, do not include them.
            site_packages=True, 
            excludes=['tables', 'numpy'], 
            )
        )
    # Now some fixes to py2app:
    py2app_opts = setup_args['options']['py2app']
    # Fix the path to included Python extensions.
    extra_paths = \
        ['lib/python{0[0]}.{0[1]}/lib-dynload'.format(sys.version_info[:2])]
    py2app_opts['plist'] = {'PyResourcePackages': extra_paths}
    # Module dependency detection doesn't find these modules.
    py2app_opts['includes'] = ['sip']

    print >> sys.stderr, """\
.. NOTE::

   Unless explicitly removed, the application bundle will contain the example
   files included with the source.  (This will be taken into account by the
   ``macosxapp/make.sh`` script.)
"""

# Get the version number
f = open('VERSION', 'r')
vt_version = f.readline()[:-1]
f.close()

if sphinx_found:
    command_class = {'build_sphinx': BuildSphinx}
else:
    command_class = {}

setup(name = 'ViTables', # The name of the distribution
    version = "{0}".format(vt_version), 
    description = 'A viewer for PyTables package', 
    long_description = \
        """
        ViTables is a GUI for PyTables (a hierarchical database
        package designed to efficently manage very large amounts of
        data) . It allows to open arbitrarely large PyTables and HDF5
        files and browse their data and metadata in a variety of ways.

        """, 

    author = 'Vicent Mas', 
    author_email = 'uvemas@gmail.com', 
    maintainer = 'Vicent Mas', 
    maintainer_email = 'uvemas@gmail.com', 
    url = 'http://www.vitables.org', 
    license = 'GPLv3, see the LICENSE.txt file for detailed info', 
    platforms = 'Unix, MacOSX, Windows', 
    classifiers = ['Development Status :: 2.1', 
    'Environment :: Desktop', 
    'Operating System :: POSIX', 
    'Programming Language :: Python'], 
    scripts = ['scripts/vitables'], 
    packages = ['vitables', 'vitables.docBrowser', 'vitables.h5db', 
        'vitables.nodeProperties', 'vitables.queries', 'vitables.preferences', 
        'vitables.vtTables', 'vitables.vtWidgets', 'vitables.plugins', 
        'vitables.plugins.csv', 'vitables.plugins.timeseries', 
        'vitables.plugins.menu'], 
    package_data = {
        'vitables.nodeProperties': ['*.ui'], 
        'vitables.preferences': ['*.ui'], 
        'vitables.queries': ['*.ui'], 
        'vitables.vtWidgets': ['*.ui'], 
        'vitables': ['icons/*.*', 'icons/*/*.*', 'htmldocs/*.*', 
            'htmldocs/*/*.*'], 
        'vitables.plugins.csv': ['icons/*.*'], 
        'vitables.plugins.timeseries': ['*.ui', '*.ini'], 
    }, 
    cmdclass = command_class,

    **setup_args
)

# Says goodbye after building/installing IF the user didn't ask for help
# $ python setup.py install --help
# $ python setup.py sdist --help
# $ python setup.py sdist --help-formats
# $ python setup.py build --help
# $ python setup.py build --help-compiler

helpAsked = False
for item in ['-h', '--help', '--help-commands', '--help-formats',
    '--help-compiler']:
    if item in sys.argv:
        helpAsked = True
        break

if len(sys.argv) > 1 and not helpAsked:
    if sys.argv[1] == 'build' :
        print "\nBuild process completed.\n"
    elif sys.argv[1] == 'sdist' :
        print "\nSources package done.\n"
    elif sys.argv[1] == 'install' :
        print """\n
Installation completed successfully!
Enjoy Data with ViTables, the troll of the PyTables family."""
