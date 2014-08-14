Development Notes
=================

To create development environment:

.. code-block:: sh

   mkvirtualenv --system-site-packages vttest
   python setup.py develop

To generate dictionary of all datasets in all example files change dir
to ViTables folder and run:

.. code-block:: sh

   for d in arrays misc tables timeseries; do 
       d=examples/$d
       for f in `ls $d`; do
           f=$d/$f
           echo \'$f\': [
	   for n in `h5ls -r -S $f | grep 'Dataset' | sed s/\\\\\\\\\ /%/g | cut -f 1 -d ' ' | cut  -c 2-`; do
	       n=`echo $n | sed s/%/\ /g`
	       echo "    " \'$n\',
	   done
	   echo ],;
       done
   done

Installation
------------

Windows
+++++++

The easiest way to create a standalone windows installer is to use
WinPython and InnoSetup. A good description of the process was written
by `Cyrille Rossant
<http://cyrille.rossant.net/create-a-standalone-windows-installer-for-your-python-application/>`_.
The installer will create a single folder in `Program Files` that
contains Python and all required modules. There is currently a problem
with PyQt installation. That is if a different version of PyQt is
installed in the system then ViTables might crush on some functions.
There is a version of ViTables already installed in WinPython so if
old version is enough one can skip the steps below.

Applied to ViTable the procedure has the following steps:

1. Download source a ViTables source distribution. It is also possible
   to make one from the develop branch by executing the following command:

   .. code-block:: sh
      
      python setup.py sdist

2. Install InnoSetup. 

3. Download 32-bit version of WinPython that contains Python
   2.7. ViTables might work with Python 3 but was not tested atm.

4. Create `ViTables` folder and install WinPython in it.

5. Configure WinPython using `WinPython Control Panel.exe` that can be
   found inside installed WinPython. Remove ViTables from the
   installation and new `.tar.gz`.

6. Copy `vitables_setup.iss` from `mswindows` folder of ViTables
   development branch into the folder that contains ViTables dir with
   WinPython.

7. Open `vitables_setup.iss` and replace WinPython and python version
   numbers in the line

   .. code-block:: text

      #define pydir "WinPython-32bit-2.7.6.4\python-2.7.6"`.

8. Compile `vitables_setup.iss`, the installer will be placed into
   `Output` dir.


If Python 2.7 along with PyQt, future and numpy is already present
in the system then it is possible to install ViTables directly:

1. Clone development branch or download a source distribution that is
   based on it.

2. Switch to ViTables folder and run

   .. code-block:: sh
      
      python setup.py bdist_wininst

3. The installer will be created in `dist` folder. It can be used to
   install ViTables on a system that have Python and required
   libraries.

Plugins
-------

i18n
++++

1. Create module project file

   .. code-block:: text

        TRANSLATIONS = plugin_ru_RU.ts

        SOURCES = plugin/configure.py \
                  plugin/analyze.py

   
2. Run ``pylupdate4`` to create ``.ts`` file in top level folder:
   
   .. code-block:: sh

       pylupdate4 plugin.pro

3. Translate using ``linguist`` and store compiled version in, for
   example, ``i18n/plugin_ru_RU.qm``.

4. Create ``resources.qrc`` with resource description:

   .. code-block:: xml

        <!DOCTYPE RCC><RCC version="1.0">
        <qresource>
            <file>i18n/plugin_ru_RU.qm</file>
        </qresource>
        </RCC>

5. Compile resource

   .. code-block:: sh

       pyrcc4 -o plugin/resources.py resources.qrc

6. Add the following to plugin class level code:

   .. code-block:: python

        locale_name = qtcore.QLocale.system().name()
        translator = qtcore.QTranslator()
        if not translator.load(':/i18n/plugin_{0}.qm'.format(locale_name)):
             translator = None
