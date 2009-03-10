# This Makefile is only intended to prepare for distribution the ViTables
# sources imported from a repository.  For building and installing ViTables,
# please use ``setup.py`` as described in the ``INSTALL.txt`` file.

.PHONY:	vtdoc

vtdoc:
	cd ./doc && make

resources: vtdoc resources.qrc
	pyrcc4 -o vitables/qrc_resources.py resources.qrc

uis:
	pyuic4 -o vitables/queries/queryUI.py vitables/queries/query_dlg.ui
	pyuic4 -o vitables/preferences/settingsUI.py vitables/preferences/settings_dlg.ui

unix: resources uis
	python setup.py sdist

clean:
	cd ./doc && make clean
	-rm -f vitables/qrc_resources.py
	-rm -f vitables/qrc_resources.pyc
	-rm -f vitables/queries/queryUI.py
	-rm -f vitables/queries/queryUI.pyc
	-rm -f vitables/preferences/settingsUI.py
	-rm -f vitables/preferences/settingsUI.pyc
	-rm -f MANIFEST
	-rm -rf build dist
