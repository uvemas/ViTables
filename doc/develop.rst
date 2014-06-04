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


Plugin i18n
-----------

1. Create module project file

   .. code-block:: text

        TRANSLATIONS = plugin_ru_RU.ts

        SOURCES = plugin/configure.py \
                  plugin/analyze.py

   
2. Run `pylupdate4` to create `.ts` file in top level folder.

3. Translate and store compiled version in, for example, `i18n/plugin_ru_RU.qm`.

4. Create `resources.qrc` with resource description:

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
