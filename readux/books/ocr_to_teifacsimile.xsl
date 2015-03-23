<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:alto="http://www.loc.gov/standards/alto/ns-v2#"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  xmlns:fr8="http://www.abbyy.com/FineReader_xml/FineReader8-schema-v2.xml"
  xmlns:fr6="http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml"
  xmlns="http://www.tei-c.org/ns/1.0" version="2.0" exclude-result-prefixes="tei xs alto fr8 fr6">

  <!--Identity transform written to create TEI files using Alto data.-->
  <doc xmlns="http://www.oxygenxml.com/ns/doc/xsl">
    <desc>Identity stylesheet for generating TEI for Sacred Harp docs. </desc>
  </doc>

  <xsl:strip-space elements="*"/>
  <xsl:output indent="yes" method="xml" encoding="utf-8" omit-xml-declaration="no"/>

  <xsl:template match="text()"><xsl:value-of select="normalize-space(.)"/></xsl:template>

  <xsl:template match="/">
    <TEI>
      <teiHeader>
        <fileDesc>
          <titleStmt>
            <title>placeholder</title>
            <respStmt>
              <resp>-</resp>
              <name>-</name>
            </respStmt>
          </titleStmt>
          <publicationStmt>
            <distributor>Emory University</distributor>
          </publicationStmt>
          <sourceDesc>
          </sourceDesc>
        </fileDesc>
      </teiHeader>
      <xsl:apply-templates/>
    </TEI>
  </xsl:template>


  <!-- template mathes for mets/alto elements -->

  <xsl:template match="alto:Description"/>

  <xsl:template match="alto:Layout">
    <xsl:element name="facsimile">
      <xsl:attribute name="xml:id">fn<xsl:value-of select="substring-before(preceding::fileName,'.jpg')"/>fcs.<xsl:value-of select="generate-id()"/></xsl:attribute>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="alto:Page">
    <xsl:element name="surface">
      <xsl:attribute name="xml:id">fn<xsl:value-of select="substring-before(preceding::fileName,'.jpg')"/>pg.<xsl:value-of select="generate-id()"/></xsl:attribute>
      <xsl:attribute name="type">page</xsl:attribute>
      <xsl:attribute name="ulx">0</xsl:attribute>
      <xsl:attribute name="uly">0</xsl:attribute>
      <xsl:attribute name="lrx"><xsl:value-of select="@WIDTH"/></xsl:attribute>
      <xsl:attribute name="lry"><xsl:value-of select="@HEIGHT"/></xsl:attribute>
      <xsl:element name="graphic">
        <xsl:attribute name="url"><xsl:value-of select="preceding::fileName"></xsl:value-of></xsl:attribute>
      </xsl:element>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="alto:TextBlock">
    <xsl:element name="zone">
      <xsl:attribute name="xml:id">fn<xsl:value-of select="substring-before(preceding::fileName,'.jpg')"/>tbk.<xsl:value-of select="generate-id()"/></xsl:attribute>
      <xsl:attribute name="type">textBlock</xsl:attribute>
      <xsl:attribute name="ulx"><xsl:value-of select="@HPOS"/></xsl:attribute>
      <xsl:attribute name="uly"><xsl:value-of select="@VPOS"/></xsl:attribute>
      <xsl:attribute name="lrx"><xsl:value-of select="@HPOS + @WIDTH"/></xsl:attribute>
      <xsl:attribute name="lry"><xsl:value-of select="@VPOS + @HEIGHT"/></xsl:attribute>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="alto:TextLine">
    <xsl:element name="zone">
      <xsl:attribute name="xml:id">fn<xsl:value-of select="substring-before(preceding::fileName,'.jpg')"/>tln.<xsl:value-of select="generate-id()"/></xsl:attribute>
      <xsl:attribute name="type">textLine</xsl:attribute>
      <xsl:attribute name="ulx"><xsl:value-of select="@HPOS"/></xsl:attribute>
      <xsl:attribute name="uly"><xsl:value-of select="@VPOS"/></xsl:attribute>
      <xsl:attribute name="lrx"><xsl:value-of select="@HPOS + @WIDTH"/></xsl:attribute>
      <xsl:attribute name="lry"><xsl:value-of select="@VPOS + @HEIGHT"/></xsl:attribute>
      <xsl:element name="line">
        <xsl:apply-templates/>
      </xsl:element>
    </xsl:element>
  </xsl:template>

  <xsl:template match="alto:SP">
    <xsl:text> </xsl:text>
  </xsl:template>

  <xsl:template match="alto:String">
    <xsl:element name="zone">
      <xsl:attribute name="xml:id">fn<xsl:value-of select="substring-before(preceding::fileName,'.jpg')"/>str.<xsl:value-of select="generate-id()"/></xsl:attribute>
      <xsl:attribute name="type">string</xsl:attribute>
      <xsl:attribute name="ulx"><xsl:value-of select="@HPOS"/></xsl:attribute>
      <xsl:attribute name="uly"><xsl:value-of select="@VPOS"/></xsl:attribute>
      <xsl:attribute name="lrx"><xsl:value-of select="@HPOS + @WIDTH"/></xsl:attribute>
      <xsl:attribute name="lry"><xsl:value-of select="@VPOS + @HEIGHT"/></xsl:attribute>
      <xsl:element name="w">
        <xsl:value-of select="@CONTENT"/>
      </xsl:element>
    </xsl:element>
  </xsl:template>

  <xsl:template match="alto:Illustration">
  <xsl:element name="zone">
    <xsl:attribute name="xml:id">fn<xsl:value-of select="substring-before(preceding::fileName,'.jpg')"/>ill.<xsl:value-of select="generate-id()"/></xsl:attribute>
    <xsl:attribute name="type">illustration</xsl:attribute>
    <xsl:attribute name="ulx"><xsl:value-of select="@HPOS"/></xsl:attribute>
    <xsl:attribute name="uly"><xsl:value-of select="@VPOS"/></xsl:attribute>
    <xsl:attribute name="lrx"><xsl:value-of select="@HPOS + @WIDTH"/></xsl:attribute>
    <xsl:attribute name="lry"><xsl:value-of select="@VPOS + @HEIGHT"/></xsl:attribute>
  </xsl:element>
</xsl:template>

  <!-- template matches for abbyy finereader elements -->

    <xsl:template match="fr8:page|fr6:page">
    <xsl:element name="facsimile">


    <xsl:element name="surface">
      <xsl:attribute name="xml:id">pg.<xsl:value-of select="format-number(position(), '0000')"/></xsl:attribute>
      <xsl:attribute name="type">page</xsl:attribute>
      <xsl:attribute name="ulx">0</xsl:attribute>
      <xsl:attribute name="uly">0</xsl:attribute>
      <xsl:attribute name="lrx"><xsl:value-of select="@width"/></xsl:attribute>
      <xsl:attribute name="lry"><xsl:value-of select="@height"/></xsl:attribute>
      <xsl:element name="graphic">
        <xsl:attribute name="url">
          <!--add graphic filename-->
        </xsl:attribute>
      </xsl:element>
      <xsl:apply-templates/>
    </xsl:element>

      </xsl:element>

  </xsl:template>

   <xsl:template match="fr8:block|fr6:block">
    <xsl:element name="zone">
      <xsl:attribute name="xml:id">bk.<xsl:value-of select="generate-id()"/></xsl:attribute>
      <xsl:attribute name="type"><xsl:value-of select="@blockType"/></xsl:attribute>
      <xsl:attribute name="ulx"><xsl:value-of select="@l"/></xsl:attribute>
      <xsl:attribute name="uly"><xsl:value-of select="@t"/></xsl:attribute>
      <xsl:attribute name="lrx"><xsl:value-of select="@r"/></xsl:attribute>
      <xsl:attribute name="lry"><xsl:value-of select="@b"/></xsl:attribute>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="fr8:line|fr6:line">
    <xsl:element name="zone">
      <xsl:attribute name="xml:id">ln.<xsl:value-of select="generate-id()"/></xsl:attribute>
      <xsl:attribute name="type">line</xsl:attribute>
      <xsl:attribute name="ulx"><xsl:value-of select="@l"/></xsl:attribute>
      <xsl:attribute name="uly"><xsl:value-of select="@t"/></xsl:attribute>
      <xsl:attribute name="lrx"><xsl:value-of select="@r"/></xsl:attribute>
      <xsl:attribute name="lry"><xsl:value-of select="@b"/></xsl:attribute>
      <xsl:element name="line">
      <xsl:value-of select="normalize-space(.)"/>
      </xsl:element>
    </xsl:element>
  </xsl:template>


</xsl:stylesheet>
