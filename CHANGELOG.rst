.. _CHANGELOG:

CHANGELOG
=========

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