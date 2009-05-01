#!/usr/bin/env python

#----------------------------------------------------------------------
# Setup script for the vitables package

import sys
import os
import glob

from distutils.core import setup
from distutils.command.install_data import install_data

use_py2app = False
if sys.platform == 'darwin' and 'py2app' in sys.argv:
    import py2app
    use_py2app = True

def checkVersions():
    """Check libraries availability.

    If a required library is not installed or it is too old then the setup
    process is aborted.
    """

    # Check if PyTables and PyQt are installed
    try:
        from tables import __version__
        from PyQt4.QtCore import qVersion, PYQT_VERSION_STR
    except ImportError, e:
        print e
        sys.exit()

    # Check versions
    pyVersion = sys.version_info
    if pyVersion < (2, 5) :
        print "###############################################################"
        print "You need Python 2.5 or greater to run ViTables!. Exiting..."
        print "###############################################################"
        sys.exit(1)

    tablesVersion = __version__
    if tablesVersion < '2.0' :
        print "###############################################################"
        print "You need PyTables 2.0 or greater to run ViTables!. Exiting..."
        print "###############################################################"
        sys.exit(1)

    qtVersion = qVersion()
    if qtVersion < '4.4' :
        print "###############################################################"
        print "You need Qt v4.4 or greater to run ViTables!. Exiting..."
        print "###############################################################"
        sys.exit(1)

    pyqtVersion = PYQT_VERSION_STR
    if pyqtVersion < '4.4' :
        print "###############################################################"
        print "You need PyQt v4.4 or greater to run ViTables!. Exiting..."
        print "###############################################################"
        sys.exit(1)

# =================================================================

# Customized install_data command. It creates a vitables module with
# two attributes that will be used for configuring the application at
# runtime.  This class is not used by py2app, which is OK, since the
# vtSite.py included in sources is intelligent enough for the
# packaged Mac OS X app.
class smart_install_data(install_data):
    def run(self):
        install_cmd = self.get_finalized_command('install')

        # The project installation directory can be set via --install-purelib
        # and some other options
        install_lib_dir = getattr(install_cmd, 'install_lib')
        tmp = install_lib_dir.replace(chr(92),'/')

        install_options = install_cmd.distribution.command_options["install"]
        # If data directory is not specified (via configuration file
        # or command line argument)...
        if not install_options.has_key('install_data'):
            # Data will not be located in the $base directory (default
            # behavior) but in the project directory
            install_data_dir = os.path.join(install_lib_dir, 'vitables')
            setattr(self, 'install_dir', install_data_dir)
        else:
            # Data directory is specified via configuration file or
            # or command line argument
            install_data_dir = getattr(install_cmd, 'install_data')

        # Create the module vtSite.py.
        # The module has the attribute INSTALLDIR
        # When installing this module will overwrite that included
        # in the source package and will be used at runtime
        vtpaths_module = open(os.path.join(install_lib_dir,
            'vitables', 'vtSite.py'), 'w')
        # If we are not installing ViTables but packaging it using a
        # chrooted environment then the path to the chrooted environment
        # shouldn't be included in the module attributes because this
        # path will not exist in the installation target directory
        if self.root != None:
            tmp = tmp[len(self.root):]
            install_data_dir = install_data_dir[len(self.root):]
        installdir = os.path.join(os.path.normpath(tmp), 
                                  'vitables').replace(chr(92),'/')
        vtpaths_module.write('INSTALLDIR = "%s"\n' % installdir)
        vtpaths_module.close()

        return install_data.run(self)

# =================================================================

# =================================================================
# Helper function to add icons in UNIX platforms that support the
# FreeDesktop guidelines (http://standards.freedesktop.org). In
# particular, it is based on the 0.6 version of the basedir specs
# (http://standards.freedesktop.org/basedir-spec) and version 0.11 of
# the icon theme specs
# (http://www.freedesktop.org/wiki/Standards/icon-theme-spec). If you
# find quirks or have suggestions on it, please, report them back.
# F. Altet 2006-02-22
def unix_icon_dir_lookup():

    data_dirs_list = []
    data_dirs = ''
    if os.getuid() == 0:  # Running as root!
        # Check for a XDG_DATA_DIRS environment variable, just in case the
        # WM is installed in a non-standard place.
        if 'XDG_DATA_DIRS' in os.environ:
            data_dirs = os.environ['XDG_DATA_DIRS']
        else:
            # Check whether we should install data in /usr/local or /usr
            for data_dir in ['/usr/local/share', '/usr/share']:
                if (os.path.isdir(os.path.join(data_dir, 'icons/hicolor')) and
                    os.path.isdir(os.path.join(data_dir, 'applications'))):
                    data_dirs_list.append(data_dir)
            data_dirs = ":".join(data_dirs_list)
    else:  # The user is installing as a non-privilegied uid
        # Check if the user can write in any of the XDG_DATA_DIRS
        if 'XDG_DATA_DIRS' in os.environ:
            for data_dir in os.environ['XDG_DATA_DIRS'].split(':'):
                if os.access(data_dir, os.W_OK):
                    data_dirs_list.append(data_dir)
        if data_dirs_list != []:
            # He can write. Choose this as the installation place.
            data_dirs = ":".join(data_dirs_list)
# It is not clear to me whether this is a standard or not. I'll disable
# this until I can collect more info about this issue.
#         else:
#             # He cannot write there or there are no XDG_DATA_DIRS.
#             # Try to save icons in the $HOME/.local/share
#             local_dir = os.path.join(os.environ['HOME'], ".local")
#             if not os.path.exists(local_dir):
#                 os.mkdir(local_dir)
#             share_dir = os.path.join(local_dir, "share")
#             if not os.path.exists(share_dir):
#                 os.mkdir(share_dir)
#             if os.path.isdir(share_dir):
#                 data_dirs = share_dir

    return data_dirs

# Main function to add icons in UNIX platforms
def add_unix_icons():

    data_dirs = unix_icon_dir_lookup()
    if data_dirs != "":
        # Great!, we have found something appropriate to write
        # Select the first directory found
        data_dir = data_dirs.split(':')[0]
        # Copy there the icons
        # First, the bitmap ones
        # The bitmap icons doesn't seems to be necessary, as both KDE and Gnome
        # seems to support scalable icons
#         for size in ["16x16", "22x22", "32x32", "48x48", "64x64", "128x128"]:
#             fname = "unixapp/vitables_%s.png" % (size)
#             dname = os.path.join(data_dir, "icons/hicolor/%s/apps" % (size))
#             if os.path.isdir(dname):
#                 destname = os.path.join(dname, "vitables.png")
#                 print "@copying cp %s -> %s" % (fname, destname)
#                 os.system("cp %s %s" % (fname, destname))
        # Then, the scalable icon
        dname = os.path.join(data_dir, "icons/hicolor/scalable/apps")
        if os.path.isdir(dname):
            print "@copying %s -> %s" % ("unixapp/vitables.svgz", dname)
            os.system("cp %s %s" % ("unixapp/vitables.svgz", dname))
        # Finally, the .desktop file
        dname = os.path.join(data_dir, "applications")
        if os.path.isdir(dname):
            print "@copying %s -> %s" % ("unixapp/vitables.desktop", dname)
            os.system("cp %s %s" % ("unixapp/vitables.desktop", dname))
    else:
        print >> sys.stderr, """\
.. NOTE::

   The installer was unable to find sensible places to put the desktop icon
   for ViTables. If you want to create a desktop link to ViTables you can find
   the needed files (.desktop and icon) in the icons/ directory.

"""
# End of the code to add the application icons in Unix systems.
# =================================================================


helpAsked = False
for item in ['-h', '--help', '--help-commands', '--help-formats',
    '--help-compiler']:
    if item in sys.argv:
        helpAsked = True
        break

if not helpAsked:
    checkVersions()

# Proceed if required libraries are OK

# Get the version number
f = open('VERSION', 'r')
vt_version = f.readline()[:-1]
f.close()

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

setup(name = 'ViTables', # The name of the distribution
    version = "%s" % vt_version,
    description = 'A viewer for pytables package',
    long_description = \
        """
        ViTables is a GUI for PyTables (a hierarchical database
        package designed to efficently manage very large amounts of
        data) . It allows to open arbitrarely large PyTables and HDF5
        files and browse its data and metadata in a variety of ways.

        """,

    author = 'Vicent Mas',
    author_email = 'uvemas@gmail.com',
    maintainer = 'Vicent Mas',
    maintainer_email = 'uvemas@gmail.com',
    url = 'http://www.vitables.org',
    license = 'GPLv3, see the LICENSE.txt file for detailed info',
    platforms = 'Unix, MacOSX, Windows',
    classifiers = ['Development Status :: 2.0',
    'Environment :: Desktop',
    'Operating System :: POSIX',
    'Programming Language :: Python'],
    packages = ['vitables', 'vitables.docBrowser',
    'vitables.h5db', 'vitables.nodeProperties', 'vitables.queries', 
    'vitables.preferences', 'vitables.plugins', 
    'vitables.vtTables', 'vitables.vtWidgets'],
    scripts = ['scripts/vitables'],
    cmdclass = {"install_data":smart_install_data},
    data_files = [
    ('examples', glob.glob('examples/*.h5')),
    ('examples/arrays', glob.glob('examples/arrays/*.h5')),
    ('examples/misc', glob.glob('examples/misc/*.h5')),
    ('examples/scripts', glob.glob('examples/scripts/*.py')),
    ('examples/tables', glob.glob('examples/tables/*.h5')),
    ('examples/tests', glob.glob('examples/tests/*.h5')),
    ('examples/timeseries', glob.glob('examples/timeseries/*.h5')),
    ('doc', glob.glob('doc/*.pdf')),
    ('', ['LICENSE.txt', 'LICENSE.html']),
    ('', ['VERSION'])
    ],

    **setup_args
)

# Says goodbye after building/installing IF the user didn't asked for help
# $ python setup.py install --help
# $ python setup.py sdist --help
# $ python setup.py sdist --help-formats
# $ python setup.py build --help
# $ python setup.py build --help-compiler

if len(sys.argv) > 1 and not helpAsked:
    if sys.argv[1] == 'build' :
        print "\nBuild process completed.\n"
    elif sys.argv[1] == 'sdist' :
        print "\nSources package done.\n"
    elif sys.argv[1] == 'install' :
        # Finally, copy the icons if we are on Unix systems, except MacOSX.
        if os.name == "posix" and sys.platform != 'darwin':
            add_unix_icons()
        print """\n
Installation completed successfully!
Enjoy Data with ViTables, the troll of the PyTables family."""


