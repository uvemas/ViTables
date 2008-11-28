# This Makefile is only intended to prepare for distribution the ViTables
# sources imported from a repository.  For building and installing ViTables,
# please use ``setup.py`` as described in the ``INSTALL.txt`` file.

#.PHONY:	vtdoc

vtdoc:
	cd ./doc && make

unix: vtdoc
	python setup.py sdist

clean:
	cd ./doc && make clean
	-rm -f MANIFEST
	-rm -rf build dist
