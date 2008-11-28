#!/bin/sh
set -e

VER=$(cat ../VERSION)

PYVERS="$(ls /Library/Frameworks/Python.framework/Versions | grep -v Current)"
if [ ! "$PYVERS" ]; then
	echo "No available Python installs." > /dev/stderr
	exit 1
fi

if [ "$1" = "clean" ]; then
	cleaning=true
fi


if [ $cleaning ]; then
	rm -f vitables-app.py
else
	cp ../scripts/vitables vitables-app.py
fi

for PYVER in $PYVERS; do
	if ! python$PYVER -c 'import tables' 2> /dev/null; then
		continue
	fi

	rm -rf ../dist/ViTables.app
	if [ ! $cleaning ]; then
		echo "Creating application bundle for Python $PYVER..."
		(cd .. && python$PYVER setup.py py2app)
	fi

	DMGDIR="ViTables $VER (py$PYVER)"
	DMG="ViTables-${VER}.macosxppc-py${PYVER}.dmg"
	RESOURCES="$DMGDIR/ViTables.app/Contents/Resources"

	if [ $cleaning ]; then
		rm -rf "$DMGDIR" "$DMG"
		continue
	fi

	echo -n "Building $DMG..."
	echo -n " app"
	mkdir -p "$DMGDIR"
	cp -R ../dist/ViTables.app "$DMGDIR"
	echo -n " examples"
	mv "$RESOURCES/examples" "$DMGDIR/Examples"
	echo -n " license"
	cp ../LICENSE.* "$RESOURCES"
	cp ../LICENSE.txt "$DMGDIR/License.txt"
	echo -n " readme"
	cp ../README.txt "$DMGDIR/ReadMe.txt"
	sed -e "s/@VER@/$VER/g" -e "s/@PYVER@/$PYVER/g" < ReadMe-MacOSX.rtf > "$DMGDIR/ReadMe-MacOSX.rtf"
	echo -n " guide"
	cp ../doc/usersguide.pdf "$DMGDIR/User's Guide.pdf"
	cp -R ../doc/html "$DMGDIR/User's Guide (HTML)"
	echo "."
	hdiutil create -srcfolder "$DMGDIR" -anyowners -format UDZO -imagekey zlib-level=9 "$DMG"
done
echo "Done"
