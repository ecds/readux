.. _CHANGELOG:

CHANGELOG
=========

Release 1.6 - Group Annotation
------------------------------

* As a site administrator I want to create and manage annotation groups
  of existing users so that I can support group annotation projects.
* As a logged in user I want to see annotations shared with groups I
  belong to so that I can collaborate with other members of those groups.
* As a logged in user when I am making an annotation I want to grant
  annotation groups access to read, edit, or delete my annotation so
  that I can collaborate with group members.
* As a logged in user, I want to see an indication when an annotation
  is shared with a group.
* As a logged in user, I want to see who authored an annotation so that
  I can easily distinguish my annotations from those shared with groups
  I belong to.
* As a logged in user, I can only update annotation permissions if
  I have the admin annotation permission, so that full access to editing
  and deleting annotations can be controlled.
* As a logged in user when I export a volume I want to choose between
  exporting only my annotations or all annotations in a group I belong
  to so that I can export an individual or collaborative project.
* Now using `django-guardian <https://github.com/django-guardian/django-guardian>`_
  for per-object annotation permissions.
* Includes a new annotator permissions Javasscript module (included in
  readux codebase for now).
* Data migrations to clean up redundant data in annotation extra data
  JSON field and grant default annotation author permissions.

Release 1.5.1
-------------

* Reference final released versions of annotator-meltdown and
  annotator-meltdown-zotero

Release 1.5 - Enhanced Annotation
---------------------------------

* As a researcher I want to make internal references to other pages in
  order to show connections to other parts of the same work.
* As a researcher I want to include audio in my annotations so I can
  demonstrate audible differences in the content.
* As a researcher I want to include video in my annotations so I can
  associate enriched media with volume content.
* As a researcher I want to link my Zotero account with my Readux login
  so that I can add Zotero citations to my annotations.
* As a researcher I want to look up Zotero citations and add them to my
  annotations in order to show my sources.
* As researcher I want to search the text of my annotations for the
  volume I am working on in order to find specific notes or content.
* As a site user I want to login in with Emory credentials so that
  I can easily start making annotations.
* As a user, I can find readux volume pages through a search engine,
  so I can easily find relevant content.
* TEI export now includes an encoding description in the TEI header.
* bugfix: Annotation window sometimes pops up in the top right of the
  screen, should hover near highlighted text/image.  (Actual fix in
  `annotator-marginalia <http://emory-lits-labs.github.io/annotator-marginalia/>`_)
* bugfix: Exported site browse annotations by tag never displays more
  than one annotation. (Actual fix in `digitaledition-jekylltheme <https://github.com/emory-libraries-ecds/digitaledition-jekylltheme>`_)
* Project documentation now includes technical descriptions and diagrams
  of Fedora object models and readux processes.

Release 1.4.1
-------------

* As a Readux admin, I want a record when the export feature is used so
  that I can find out who is creating exported editions.

Release 1.4 - Basic Export
--------------------------

This release adds the capability to export a single Readux volume with
annotations to create a standalone annotated website edition, using
Jekyll and with optional GitHub / GitHub Pages integration.


Export functionality
^^^^^^^^^^^^^^^^^^^^

* As an annotated edition author I want to export an edition that has TEI
  with text, image references, and annotations so that I can have a
  durable format copy of my edition with my annotation content.
* As an annotated edition author, I want to generate a web site package
  with volume content and annotations so that I can publish my digital
  edition.
* As an annotated edition author I want to generate a website package that
  can be modified so that I can customize my edition.
* As an annotated edition author, I want a website package that allows me
  to browse pages by thumbnail so that site visitor can easily select a
  page of interest.
* As an annotated edition author, I want my website edition to include
  annotation counts for each page so that my site visitors know which
  pages have annotations.
* As an annotated edition author, I want my website edition to include
  tags in the annotation display so that my site visitors can see my
  categorization.
* As an annotated edition author, I want my website edition to support
  keyword searching so that my site visitors can find content of
  interest.
* As an annotated edition author, I want to be able to customize my
  website edition’s page urls to match the number in the source text so
  that my site visitors experience an intuitive navigation of the
  edition.
* As an annotated edition author, I want the option of creating a new
  GitHub repository with my exported website edition, so that I can
  version my data and publish it on GitHub Pages.
* As an annotated edition author, I want my website edition to include
  citation information so that my site visitors can reference it properly.
* As an annotated edition author, I want to have a copy of the exported
  TEI in the website bundle so that I can see the data used to generate
  the web edition.
* As an annotated edition author, I want my website edition to include
  social media integration so that my site visitors can share content.
* As an annotated edition author, I want my website edition to be viewable
  on tablets so that my site visitors can view it on multiple devices.
* As an annotated edition author I want my website edition to include
  individual annotation pages so that users can more easily view and
  cite long form and multimedia annotation content.

Other updates
^^^^^^^^^^^^^

* As a site user, I want to link my social login accounts so that I can
  access annotations from any of my accounts.
* As an annotated edition author, I want to see an error message in the
  event that I log out while trying to export my edition so that I know
  I need to be logged in to complete the export.
* As a site user I want to see a permanent url on the pages for volume
  and single-page so that I can make stable references.
* Update latest 3.x Bootstrap and django-eultheme 1.2.1


Release 1.3.7
-------------

* As a site administrator I want to include video content in site pages
  so that I can share dynamic content like screencasts.

Release 1.3.6
-------------

* Improved regenerate-id logic for OCR, use a readux image url when
  generating page TEI.

Release 1.3.5
-------------

* Proxy all IIIF image requests through the application, to handle
  IIIF server that is not externally accessible.

Release 1.3.4
-------------

* bugfix: collection detail pagination navigation
* bugfix: id generation error in OCR/TEI xml
* Improved page mismatch detection when generating TEI from OCR
* Revised placeholder page images for covers and volume browse
* Modify update_page_arks manage command to handle the large number
  of page arks in production

Release 1.3.3
-------------

* bugfix: collection detail pagination display
* bugfix: correct page absolute url, esp. for use in annotation uris

Release 1.3 - Simple Annotation
-------------------------------

TEI Facsimile
^^^^^^^^^^^^^
* As a system administrator, I want to run a script to generate TEI
  facsimile for volumes that have pages loaded, so that I can work with
  OCR content in a standardized format.
* As a user I would like to view the TEI underlying the page view and
  annotation, so that I can understand more about how it works, and to
  understand how to use facsimile data.
* As a researcher I want to see a view of the TEI underlying the page
  view and annotation that excludes OCR for barcodes so that I can
  focus on facsimile data of scholarly importance.

Display improvements
^^^^^^^^^^^^^^^^^^^^
* As a user, I want to navigate from page view to page view without
  having to scroll down to each page view, so that I have a better
  reading experience.
* As a user, I can see the thumbnail for landscape pages when browsing
  volumes, so I can better select appropriate pages.

Annotation
^^^^^^^^^^
* As a researcher, I want to select the OCR text on a page in order to
  copy or annotate content.
* As a site user I want to filter volumes by whether or not they have
  page-level access so that I know which volumes I can read online and
  annotate.
* As a researcher I can log in to readux using social media credentials,
  so that I do not need a separate account to create annotations.
* As a researcher I want to annotate part of the text on a page in order
  to provide additional information about the text.
* As a researcher I want to annotate an image or part of an image in
  order to provide additional information about the image.
* As a researcher I want to include simple formatting in my notes to
  make them more readable.
* As a researcher I want to include images in my annotations so that
  users can see important visual materials.
* As a researcher I want to tag annotations so that I can indicate
  connections among related content.
* As a researcher I want to edit and delete my annotations, in order to
  make changes or remove notes I no longer want.
* As a user I can see my annotations in the margin of the page, so that
  I can read all of the annotations conveniently.
* As a researcher I want to see which volumes I have annotated when I am
  browsing or searching so that I can easily resume annotating.
* As a researcher I want to see which pages I have annotated so that I
  can assess the status of my digital edition.
* As a researcher I want to make annotations anchored to stable
  identifiers that are unique across an entire volume so that I can
  maintain consistency and generate valid exports in my digital editions.
* As a user I want to see a created or last modified timestamp on
  annotations so that I know when they were last updated.
* As a user I want to see only the date created or last modified on
  annotations that are more than a week old so that I know a rough
  estimate of when they were last updated.

Annotation Administration
^^^^^^^^^^^^^^^^^^^^^^^^^
* As a site administrator I want to see which user authored an
  annotation so that I can respond to the correct user in reference to
  an annotation.
* As a site administrator, I want to view, edit, and delete annotations
  in the Django admin site so that I can manage annotations to remove
  spam or update the annotation owner.
* As a site administrator I want to click on the URI link for an
  annotation in the admin and see the annotated page in a separate
  window so that I can verify its display.

Additional Administration functionality
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* As a site administrator I want to create and edit html pages so that
  I can add content explaining the site to users.

Release 1.2.2
-------------

* Require eulfedora 1.2 for auto-checksum on ingest against Fedora 3.8

Release 1.2.1
-------------

* Update required version of django-downtime and eultheme.

Release 1.2 - Fedora 3.8 migration support
------------------------------------------

* As a site user I will see a Site Down page when maintenance is being
  performed on the site or or other circumstances that will cause the
  site to be temporarily unavailable  so that I will have an general
  idea of when I can use the site again.
* As a site user I will see a banner that displays an informative
  message on every page of the site so that I can be informed about
  future site maintenance or other events and know an approximate amount
  of any scheduled downtime.
* As an application administrator, I want to generate a list of pids for
  testing so that I can verify the application works with real data.
* Any new Fedora objects will be created with Managed datastreams instead
  of Inline for RELS-EXT and Dublin Core.
* Upgraded to Django 1.7
* Now using `django-auth-ldap <https://pythonhosted.org/django-auth-ldap/>`
  for LDAP login instead of eullocal.

Release 1.1.2
-------------

* Fix last-modified method for search results to work in cover mode.

Release 1.1.1
-------------

* Fix volume sitemaps to include both Volume 1.0 and 1.1 content models.


Release 1.1 - Import
--------------------

* As an administrative user, I want to run a script to import a volume
  and its associated metadata into the repository so that I can add new
  content to readux.
* As a user, I want to browse newly imported content and previously
  digitized content together, so that I can access newly added content
  in the same way as previously digitized materials.
* As a user I can opt to sort items on a collection browse page by date
  added, in order to see the newest material at the top of the list, so
  that I can see what is new in a collection.
* As a user, I want the option to view or download a PDF, with a warning
  for large files, so that I can choose how best to view the content.
* As an administrative user, I want to be able to run a script to load
  missing pages for a volume so that I can load all pages when the
  initial page load was interrupted.


Release 1.0.2
-------------

* As a user, I want the website to support caching so I don't have to re-download
  content that hasn't changed and the site will be faster.
* bugfix: fix indexing error for items with multiple titles
* error-handling & logging for volumes with incomplete or invalid OCR XML
* adjust models to allow eulfedora syncrepo to create needed content model objects

Release 1.0.1
-------------

* Include *.TIF in image file patterns searched when attempting to identify
  page images in **import_covers** and **import_pages** scripts
* Additional documentation and tips for running **import_covers** and
  **import_pages** scripts
* Bugfix: workaround for pdfminer maximum recursion error being triggered by
  outline detection for some PDF documents
* Enable custom 404, 403, and 500 error pages based on eultheme styles

Release 1.0 - Page-Level Access
-------------------------------

Cover images and list view improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* As a researcher, when I'm viewing a list of titles, I want the option to
  toggle to a cover view as an alternate way to view the content.
* As a user, when I toggle between cover and list views I want to be able to
  reload or go back in history without needing to reselect the mode I was last
  viewing, so that the site doesn't disrupt my browsing experience.
* As a user, when I page through a collection or search results, I expect the
  display to stay in the mode that I've selected (covers or list view), so that
  I don't have to reselect it each time.

Volume landing page and Voyant improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* As a user when I select a title in the list view, I first see an information
  page about the item, including pdf and page view selections, so that I know
  more about the item before I access it.
* As a user, I want to be able to see the full title of a book without longer
  titles overwhelming the page, so I can get to the information I want
  efficiently.
* As a researcher, I want to pass a text to Voyant for analysis in a way that
  takes advantage of caching, so that if the text has already been loaded in
  Voyant I won't have to wait as long.
* As a reseacher, I can easily read a page of text in Voyant, because the text
  is neatly formatted, so that I can more readily comprehend the text.
* As a user, I can see how large a pdf is before downloading it so that I can
  make appropriate choices about where and how to view pdfs.
* As a user, when I load a pdf I want to see the first page with content rather
  than a blank page, so that I have easier access with less confusion.

Page-level access / read online
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* As a researcher, I can page through a book viewing a single page at a time in
  order to allow viewing the details or bookmarking individual pages.
* As a user, when I'm browsing a collection or viewing search results, I can
  select an option to read the book online if pages are available, so that I can
  quickly access the content.
* As a researcher, I want the option to view pages as thumbnails to enhance
  navigation.
* As a researcher, when I'm browsing page image thumbnails I want to see an
  indicator when there's an error loading an image so that I don't mistake
  errors for blank pages.
* As a researcher, I want to be able to toggle to a mode where I can zoom in on
  an image so that I can inspect the features of a page.
* As a user, I want to be able to distinguish when I can and cannot use the zoom
  function, so I can tell when the feature is unavailable (e.g., due to image
  load error).
* As a researcher, I want to search within a single book so that I can find
  specific pages that contain terms relevant to my research.

Navigation improvements
^^^^^^^^^^^^^^^^^^^^^^^
* As a user, I want to see a label or source information for the collection
  banner image so that I know where the image comes from.
* As a user, I want to be able to identify a resource in an open tab by title,
  so I can quickly select the correct tab when using multiple tabs.
* As a user, when paging through a collection list or viewing a set of pages in
  the reading view, I can find the web page navigation at the top or bottom of
  the page, so that I do not have to scroll far to click to go to another web
  page in the series.

Integrations with external services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* As a twitter user, when I tweet a link to a readux collection, book, or page
  image, I want a preview displayed on twitter so that my followers can see
  something of the content without clicking through.
* As a facebook user, when I share a link to a readux collection, book, or page
  image, I want a preview displayed on facebook so that my friends can see
  something of the content without clicking through.
* A search engine crawling the readux site will be able to obtain basic semantic
  data about collections and books on the site so the search engine’s results
  can be improved.
* A search engine can harvest information about volume content via site maps in
  order to index the content and make it more discoverable.


Release 0.9 - PDF Access
-------------------------

* As a researcher, I want to browse a list of collections in order to
  select a subset of items to browse.
* As a researcher, I want to browse through a paginated list of all the
  books in a single collection in order to see the range of materials
  that are present.
* As a researcher, when looking at a list of books in a collection, I
  can view a PDF using my native PDF browser in order to view the
  contents of the book.
* As a researcher, I can search by simple keyword or phrase in order to
  find books that fit my interests.
* A search engine can harvest information about site content via site
  maps in order to index the content and make it more discoverable.
* As a researcher, I can select a text and pass it to Voyant to do text
  analysis for the purposes of my research.
* As a researcher, I want to be able to harvest contents into my Zotero
  library in order to facilitate research.
* As a researcher browsing a list of titles in a collection or search
  results, I want to see the author name and the year of publication
  so that if I am looking for a particular title or edition I have more
  information to identify it quickly without opening the pdf.
* As a researcher viewing keyword search results, I want to see titles
  or authors with matching terms higher in the list so that if I am
  searching for a title or author by keyword the item appears on the first
  or second page of results, and I don't have to page through all the
  results to find what I am looking for.
* As a user I can see a logo for the site, so I visually recognize that
  I am in a coherent site whenever I see it.
* As a user I see university branding on the site, so that I know that
  it is an Emory University resource.
* As a user I want to read a brief description of the content of a collection
  on the collection list page and individual collection pages, so that
  I can determine my level of interest in it.
* As an admin user, I want to be able to login with my Emory LDAP account
  so that I can re-use my existing credentials.
* As a user I can view a list of collections on the landing page by thumbnail
  image so that I can select an area of interest from visual cues.
* As a user, when viewing a single collection, I can see a visual cue of
  the collection's content, so that I can connect the item I see on the
  list view to the page I am viewing.
* As a researcher I can filter search results by collection facets, in
  order to see the material most relevant to my interests.
* As an admin, I can upload images and associate them with collections,
  so that I can manage thumbnail and splash images displayed on collection
  browse and display pages.