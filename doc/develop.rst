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
