<?xml version='1.0' encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

    <!-- The base stylesheets -->
    <xsl:import href="http://docbook.sourceforge.net/release/xsl/current/html/chunk.xsl"/>
    <xsl:include href="../custom_common.xsl"/>

    <!-- The output encoding -->
    <xsl:param name="chunker.output.encoding" select="'UTF-8'"></xsl:param>

    <!-- The CSS location -->
    <xsl:param name="html.stylesheet.type">text/css</xsl:param>
    <xsl:param name="html.stylesheet" select="'./usersguide_style.css'"></xsl:param>

    <!-- ADMONITION -->
    <!-- * use graphical admonitions in PNG format -->
    <xsl:param name="admon.graphics" select="1"></xsl:param>
    <xsl:param name="admon.graphics.extension" select="'.png'"></xsl:param>

    <!-- Generate a separate HTML page for each preface, chapter or
     appendix. -->
    <xsl:param name="chunk.section.depth" select="0"></xsl:param>

    <!-- Number all sections in the style of 'CH.S1.S2 Section Title' where
     CH is the chapter number,  S1 is the section number and S2 is the
     sub-section number.  The lables are not limited to any particular
     depth and can go as far as there are sections. -->
    <xsl:param name="section.autolabel" select="1"></xsl:param>
    <xsl:param name="section.label.includes.component.label" select="0"></xsl:param>

</xsl:stylesheet>
