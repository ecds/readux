<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:alto="http://www.loc.gov/standards/alto/ns-v2#"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  xmlns:fr8="http://www.abbyy.com/FineReader_xml/FineReader8-schema-v2.xml"
  xmlns:fr6="http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml"
  xmlns="http://www.tei-c.org/ns/1.0" version="2.0" exclude-result-prefixes="xsl xs alto fr8 fr6">

  <!-- prefix for ids, to ensure they are unique -->
  <xsl:param name="id_prefix"/>


  <!-- transform to add ids to Alto or abbyy OCR -->
  <doc xmlns="http://www.oxygenxml.com/ns/doc/xsl">
    <desc>Stylesheet for adding ids to Abbyy OCR xml or Mets/Alto.</desc>
  </doc>

  <!-- identity transform -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- ids for page elements -->
  <xsl:template match="alto:Page|fr8:page|fr6:page">
    <xsl:copy>
       <xsl:attribute name="xml:id"><xsl:value-of select="concat($id_prefix, '.p.',
          generate-id())"/></xsl:attribute>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- ids for block elements -->
  <xsl:template match="alto:TextBlock|fr8:block|fr6:block">
    <xsl:call-template name="copy-with-id">
      <xsl:with-param name="prefix" select="'b'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ids for line elements -->
  <xsl:template match="alto:TextLine|fr8:line|fr6:line">
    <xsl:call-template name="copy-with-id">
      <xsl:with-param name="prefix" select="'ln'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ids for alto elements without corresponding abbyy finereader els -->
  <xsl:template match="alto:Layout">
    <xsl:call-template name="copy-with-id">
      <xsl:with-param name="prefix" select="'l'"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="alto:String">
    <xsl:call-template name="copy-with-id">
      <xsl:with-param name="prefix" select="'s'"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="alto:Illustration">
    <xsl:call-template name="copy-with-id">
      <xsl:with-param name="prefix" select="'ill'"/>
    </xsl:call-template>
  </xsl:template>

  <!-- named template with common logic: copy node, generating a new id and
       with a prefix -->
  <xsl:template name="copy-with-id">
    <xsl:param name="prefix"/>
    <xsl:copy>
      <!-- generate an id if there is not already one present -->
      <xsl:if test="not(@xml:id)">
        <xsl:attribute name="xml:id"><xsl:value-of select="concat($id_prefix, '.',
          $prefix, '.', generate-id())"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
