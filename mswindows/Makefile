# This Makefile is intended to create the ViTables installer for Windows.
# It is not intended for distribution.

VERSIONFILE=..\VERSION
#VERSION=$(shell type ..\VERSION) (syntax not supported by nmake)

VERSION=2.1

PYTHONVERSION=26
DOTPYTHONVERSION=2.6

ROOT=..
LICENSEFILE=$(ROOT)\LICENSE.txt
LICENSEFILENAME=LICENSE.txt
WINDOWS32=C:\\Windows\\system32

# The NSIS intstaller script
VTNSIS=vitables-py$(DOTPYTHONVERSION).nsi

# ViTables executable
PYTHON=C:\Python$(PYTHONVERSION)\python
SIB="C:\Documents and Settings\vmas\Mis documentos\VendorID-1.0.0\sib\sib.py"
ICON=$(ROOT)\vitables\icons\vitables.ico

# Building the PDF documentation is currently not supported
INDEX=$(ROOT)\doc\index.rst
HTML_INDEX=$(ROOT)\doc\index_html.txt
HTML_OUTDIR=$(ROOT)\vitables\htmldocs

clean:
	del $(VTNSIS)
	del ViTables*.win32-py$(DOTPYTHONVERSION).exe
	del $(ROOT)\vitables.py
	rmdir /q /s $(ROOT)\doc\_build
	rmdir /q /s $(HTML_OUTDIR)
	del $(INDEX)
#	del $(ROOT)\doc\ViTablesUsersGuide.pdf

vitables.exe:
	copy $(ROOT)\scripts\vitables .\vitables.py
	$(PYTHON) $(SIB) -u -i $(ICON) ./vitables.py
#	$(MAKE) -C build_vitables (syntax not supported by nmake)
	cd build_vitables && $(MAKE)
	copy build_vitables\vitables.exe .
	copy build_vitables\vitables.exe.manifest .
	rmdir /q /s build_vitables
	del .\vitables.py

vtdoc:
	copy $(HTML_INDEX) $(INDEX)
	cd $(ROOT)\doc && make html
	mkdir $(HTML_OUTDIR)
	xcopy $(ROOT)\doc\_build\html\*.* /E $(HTML_OUTDIR)
	rmdir /q /s $(HTML_OUTDIR)\_sources
	copy $(ROOT)\LICENSE.html $(HTML_OUTDIR)

installer: vitables.nsi.in $(VERSIONFILE) $(LICENSEFILE) vtdoc vitables.exe
	copy ..\LICENSE.html LICENSE.html
	type vitables.nsi.in | sed -e "s/@VERSION@/$(VERSION)/g" \
	-e "s/@PYTHONVERSION@/$(PYTHONVERSION)/g" \
	-e "s/@DOTPYTHONVERSION@/$(DOTPYTHONVERSION)/g" \
	-e "s/@ROOT@/$(ROOT)/g" \
	-e "s/@WINDOWS32@/$(WINDOWS32)/g" \
	-e "s/@LICENSE@/$(LICENSE)/g" \
	-e "s/@LICENSEFILENAME@/$(LICENSEFILENAME)/g" \
	> $(VTNSIS)
	makensis $(VTNSIS)
	del LICENSE.html
	del vitables.exe
	del vitables.exe.manifest
