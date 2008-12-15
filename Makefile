# This Makefile is only intended to prepare for distribution the ViTables
# sources imported from a repository.  For building and installing ViTables,
# please use ``setup.py`` as described in the ``INSTALL.txt`` file.

#.PHONY:	vtdoc

vtdoc:
	cd ./doc && make

unix: vtdoc
	pyrcc4 -o vitables/qrc_resources.py resources.qrc
	python setup.py sdist

clean:
	cd ./doc && make clean
	-rm -f vitables/qrc_resources.py
	-rm -f MANIFEST
	-rm -rf build dist
