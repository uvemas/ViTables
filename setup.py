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
Setup script for the vitables package.
"""

import sys

from distutils.core import setup




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
        'vitables.nodeprops', 'vitables.queries', 'vitables.preferences', 
        'vitables.vttables', 'vitables.vtwidgets', 'vitables.plugins', 
        'vitables.plugins.csv', 'vitables.plugins.timeseries'], 
    package_data = {
        'vitables.nodeprops': ['*.ui'], 
        'vitables.preferences': ['*.ui'], 
        'vitables.queries': ['*.ui'], 
        'vitables.vtwidgets': ['*.ui'], 
        'vitables.plugins': ['*.ui'], 
        'vitables': ['icons/*.*', 'icons/*/*.*', 'htmldocs/*.*', 
            'htmldocs/*/*.*'], 
        'vitables.plugins.csv': ['icons/*.*'], 
        'vitables.plugins.timeseries': ['*.ui', '*.ini'], 
    }, 
    cmdclass = {},

    **setup_args
)

# Says goodbye after building/installing IF the user didn't ask for help
# $ python setup.py install --help
# $ python setup.py sdist --help
# $ python setup.py sdist --help-formats
# $ python setup.py build --help
# $ python setup.py build --help-compiler

help_asked = False
for item in ['-h', '--help', '--help-commands', '--help-formats',
    '--help-compiler']:
    if item in sys.argv:
        help_asked = True
        break

if len(sys.argv) > 1 and not help_asked:
    if sys.argv[1] == 'build' :
        print "\nBuild process completed.\n"
    elif sys.argv[1] == 'sdist' :
        print "\nSources package done.\n"
    elif sys.argv[1] == 'install' :
        print """\n
Installation completed successfully!
Enjoy Data with ViTables, the troll of the PyTables family."""
