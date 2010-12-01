# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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
import glob

from distutils.core import setup, Command
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.command.clean import clean
from distutils.dist import Distribution
from distutils.spawn import find_executable, spawn
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file



class DocbookDistribution(Distribution):
    """The distclass of this setup file.
    """
    def __init__(self, attrs=None):
        self.docbooks = None
        Distribution.__init__(self, attrs)


class BuildDocbook(Command):
    """BuildDocbook documentation and copy HTML data files.
    """

    description = "Build Docbook documentation"

    user_options = [('xsltproc-path=', None, "Path to the XSLT processor"),
        ('fop-path=', None, "Path to FOP"),
        ('xsl-style=', None, "Catalogue URI to the XSL style sheet"),
        ('fop-style=', None, "Catalogue URI for the FOP style sheet")]



    def initialize_options(self):
        self.xsltproc_path = None
        self.fop_path = None
        self.xsl_style = None
        self.fop_style = None


    def finalize_options(self):
        if self.xsltproc_path is None:
            self.xsltproc_path = find_executable("xsltproc")

        if self.fop_path is None:
            self.fop_path = find_executable("fop")

        if self.xsl_style is None:
            self.xsl_style = "./doc/custom_layer/html/custom_html.xsl"

        if self.fop_style is None:
            self.fop_style = "./doc/custom_layer/fo/custom_fo.xsl"


    def get_command_name(self):
        return 'build_doc'


    def run(self):

        """ Execute the build_doc command.

        The HTML and PDF docs are included in the tarball. So even if fop or
        xsltproc are not installed the user will be able to install ViTables
        in the usual way::

            # python setup.py install

        because the build_doc command will not abort. In a tarball installation
        the docs will never be generated, just copied to the apropriate folder.

        If user is installing a debian/ubuntu package (which will not include
        the docs, I think), in order to ensure that she will always end up with
        the docs being installed, the package should depend on the xsltproc and
        fop packages.
        """

        if self.xsltproc_path is None:
            print """Unable to find 'xsltproc', needed to generate """\
                """Docbook documentation."""
            return

        if self.fop_path is None:
            print """Unable to find 'fop', needed to generate Docbook"""\
                """documentation in PDF format."""
            return

        for input_file in self.distribution.docbooks:
            self.announce("Building Docbook documentation from %s." \
                % input_file)

            if not os.path.exists(input_file):
                raise SystemExit, "File %s is missing." % input_file

            input_file_name = os.path.splitext(input_file)[0]
            output_dir = os.path.join("vitables", "htmldocs","")

            if not os.access(output_dir, os.F_OK):
                spawn([self.xsltproc_path, "--nonet", "-o", output_dir, 
                    self.xsl_style, input_file])
                spawn([self.xsltproc_path, "--nonet", "-o", 
                    input_file_name+".fo", self.fop_style, input_file])
                spawn([self.fop_path, "-q", input_file_name+".fo", 
                    input_file_name+".pdf"])
                copy_tree(os.path.join(os.path.dirname(input_file),"images"), 
                    os.path.join(output_dir,"images"))
                copy_file('LICENSE.html', output_dir)
                copy_file("./doc/custom_layer/html/usersguide_style.css", 
                    output_dir)


def has_docbook(dbuild):
    """Return True if the `docbooks` attribute has been set.
    """
    return (dbuild.distribution.docbooks is not None and
            dbuild.distribution.docbooks != [])


class Build(build):
    """Make the commands that will build the documentation.
    """
    sub_commands = build.sub_commands[:]
    sub_commands.insert(0,('build_doc', has_docbook))

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
    extra_paths = ['lib/python%d.%d/lib-dynload' % sys.version_info[:2]]
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
    version = "%s" % vt_version, 
    distclass=DocbookDistribution, 
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
    packages = ['vitables', 'vitables.docBrowser', 'vitables.h5db', 
        'vitables.nodeProperties', 'vitables.queries', 'vitables.preferences', 
        'vitables.vtTables', 'vitables.vtWidgets', 'vitables.plugins', 
        'vitables.plugins.csv', 'vitables.plugins.menu'], 
    scripts = ['scripts/vitables'], 
    package_data = {
        'vitables.nodeProperties': ['*.ui'], 
        'vitables.preferences': ['*.ui'], 
        'vitables.queries': ['*.ui'], 
        'vitables.vtWidgets': ['*.ui'], 
        'vitables': ['icons/*.*', 'icons/*/*.*', 'htmldocs/*.*', 
            'htmldocs/*/*.*'], 
        'vitables.plugins.csv': ['icons/*.*'], 
    }, 
    cmdclass = {
          'build': Build, 
          'build_doc': BuildDocbook, 
          },
    docbooks=['doc/usersguide.xml'], 
    data_files = [
        ('examples', glob.glob('examples/*.h5')), 
        ('examples/arrays', glob.glob('examples/arrays/*.h5')), 
        ('examples/misc', glob.glob('examples/misc/*.h5')), 
        ('examples/scripts', glob.glob('examples/scripts/*.py')), 
        ('examples/tables', glob.glob('examples/tables/*.h5')), 
        ('examples/timeseries', glob.glob('examples/timeseries/*.h5')), 
        ('doc', ['doc/usersguide.xml']), 
        ('doc', ['doc/usersguide.pdf']), 
        ('', ['LICENSE.txt', 'LICENSE.html']), 
        ('plugins/csv/examples', glob.glob('plugins/csv/examples/*.csv')), 
    ], 

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
