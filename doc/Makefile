# Get all .png files
allpngs := $(wildcard images/*.png)

# Title page SVG
TPSVG=./images/title_page_plain.svg

# HTML guide stuff
HTMLDIR=html
IMAGESDIR=html/images
CSS=./pytables_style.css

# PDF guide stuff
XML_CATALOG_FILES=./custom_layer/pytables_catalog.xml
XML_DEBUG_CATALOG=1
export XML_CATALOG_FILES XML_DEBUG_CATALOG

.PHONY:		all clean

all:		usersguide.pdf html

clean:
	rm -rf $(HTMLDIR)
	rm -f usersguide.fo
	rm -f usersguide.pdf

# User's Guide in PDF format (1 file)
usersguide.pdf: usersguide.xml $(TPSVG) $(allpngs)
	xsltproc -o usersguide.fo pytables_fo.xsl usersguide.xml
	fop -q -c fop_conf.xml usersguide.fo usersguide.pdf

# User's Guide in HTML format (1 chapter per file. Stored in $HTMLDIR)
html: usersguide.xml $(allpngs)
	xsltproc pytables_html.xsl usersguide.xml
	mkdir -p $(IMAGESDIR)
	mv *.html $(HTMLDIR)
	cp $(CSS) $(HTMLDIR)
	cp images/*.png $(IMAGESDIR)
	cp not_found.html.in $(HTMLDIR)/not_found.html

