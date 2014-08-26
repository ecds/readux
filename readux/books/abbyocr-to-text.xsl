<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:fr8="http://www.abbyy.com/FineReader_xml/FineReader8-schema-v2.xml"
    version="1.0">

    <xsl:output method="text"/>
    <xsl:strip-space elements="fr8:page fr8:block fr8:region fr8:par"/>

    <!-- <xsl:template match="*">
        <xsl:apply-templates select="node()"/>
        <xsl:text> </xsl:text> 
    </xsl:template> -->

    <!--<xsl:template match="fr8:line">
        <xsl:apply-templates/><xsl:text>
</xsl:text></xsl:template>-->

</xsl:stylesheet>
