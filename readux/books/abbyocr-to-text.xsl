<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:fr8="http://www.abbyy.com/FineReader_xml/FineReader8-schema-v2.xml"
    version="1.0">

    <xsl:output method="text"/>
    <xsl:strip-space elements="fr8:page fr8:block fr8:region fr8:par fr8:cell fr8:row fr8:formatting fr8:text"/>

    <!-- long whitespace variable for use in table layout -->
    <xsl:variable name="padding"><xsl:text>                 </xsl:text></xsl:variable>

    <xsl:template match="fr8:line">
        <xsl:apply-templates/><xsl:text>
</xsl:text></xsl:template>

    <xsl:template match="fr8:block[@blockType='Table']/fr8:row">
        <xsl:apply-templates/><xsl:text>
</xsl:text>
    </xsl:template>

    <!-- add spaces at the end of cell lines based on content length to generate a more tabular layout -->
    <xsl:template match="fr8:block[@blockType='Table']//fr8:cell//fr8:line">
        <xsl:apply-templates/><xsl:value-of select="substring($padding, string-length(.))"/>
    </xsl:template>
</xsl:stylesheet>
