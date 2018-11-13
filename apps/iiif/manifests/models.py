from django.db import models
from ..kollections.models import Collection
from django.contrib.postgres.fields import JSONField
import uuid

"""
V2
{
  // Metadata about this manifest file
  "@context": "http://iiif.io/api/presentation/2/context.json",
  "@id": "http://example.org/iiif/book1/manifest",
  "@type": "sc:Manifest",

  // Descriptive metadata about the object/work
  "label": "Book 1",
  "metadata": [
    {"label": "Author", "value": "Anne Author"},
  ],
  "description": "A longer description of this example book. It should give some real information.",
  "thumbnail": {
    "@id": "http://example.org/images/book1-page1/full/80,100/0/default.jpg",
    "service": {
      "@context": "http://iiif.io/api/image/2/context.json",
      "@id": "http://example.org/images/book1-page1",
      "profile": "http://iiif.io/api/image/2/level1.json"
    }
  },

  // Presentation Information
  "viewingDirection": "right-to-left",
  "viewingHint": "paged",
  "navDate": "1856-01-01T00:00:00Z",

  // Rights Information
  "license": "http://rightsstatements.org/vocab/NoC-NC/1.0/",
  "attribution": "Provided by Example Organization",

  "logo": {
    "@id": "http://example.org/logos/institution1.jpg",
    "service": {
        "@context": "http://iiif.io/api/image/2/context.json",
        "@id": "http://example.org/service/inst1",
        "profile": "http://iiif.io/api/image/2/level2.json"
    }
  },

  // Links
  "rendering": {
    "@id": "http://example.org/iiif/book1.pdf",
    "label": "Download as PDF",
    "format": "application/pdf"
  },
  "within": "http://example.org/collections/books/",

  // List of sequences
  "sequences": [
      {
        "@id": "http://example.org/iiif/book1/sequence/normal",
        "@type": "sc:Sequence",
        "label": "Current Page Order"
        // sequence's page order should be included here, see below...
      }
      // Any additional sequences can be referenced here...
  ]
}

V3
{
  // Metadata about this manifest file
  "@context": [
    "http://www.w3.org/ns/anno.jsonld",
    "http://iiif.io/api/presentation/3/context.json"
  ],
  "id": "https://example.org/iiif/book1/manifest",
  "type": "Manifest",

  // Descriptive metadata about the object/work
  "label": { "en": [ "Book 1" ] },
  "metadata": [
    {
      "label": { "en": [ "Author" ] },
      "value": { "@none": [ "Anne Author" ] }
    },
    {
      "label": { "en": [ "Published" ] },
      "value": {
        "en": [ "Paris, circa 1400" ],
        "fr": [ "Paris, environ 1400" ]
      }
    },
    {
      "label": { "en": [ "Notes" ] },
      "value": {
        "en": [
          "Text of note 1",
          "Text of note 2"
        ]
      }
    },
    {
      "label": { "en": [ "Source" ] },
      "value": { "@none": [ "<span>From: <a href=\"https://example.org/db/1.html\">Some Collection</a></span>" ] }
    }
  ],
  "summary": { "en": [ "Book 1, written be Anne Author, published in Paris around 1400." ] },

  "thumbnail": [
    {
      "id": "https://example.org/images/book1-page1/full/80,100/0/default.jpg",
      "type": "Image",
      "service": [
        {
          "id": "https://example.org/images/book1-page1",
          "type": "ImageService3",
          "profile": "level1"
        }
      ]
    }
  ],

  // Presentation Information
  "viewingDirection": "right-to-left",
  "behavior": [ "paged" ],
  "navDate": "1856-01-01T00:00:00Z",

  // Rights Information
  "rights": "https://creativecommons.org/licenses/by/4.0/",
  "requiredStatement": {
    "label": { "en": [ "Attribution" ] },
    "value": { "en": [ "Provided by Example Organization" ] }
  },
  "logo": {
    "id": "https://example.org/logos/institution1.jpg",
    "type": "Image",
    "service": [
      {
        "id": "https://example.org/service/inst1",
        "type": "ImageService3",
        "profile": "level2"
      }
    ]
  },

  // Links
  "homepage": {
    "id": "https://example.org/info/book1/",
    "type": "Text",
    "label": { "en": [ "Home page for Book 1" ] },
    "format": "text/html"
  },
  "service": [
    {
      "id": "https://example.org/service/example",
      "type": "Service",
      "profile": "https://example.org/docs/example-service.html"
    }
  ],
  "seeAlso": [
    {
      "id": "https://example.org/library/catalog/book1.xml",
      "type": "Dataset",
      "format": "text/xml",
      "profile": "https://example.org/profiles/bibliographic"
    }
  ],
  "rendering": [
    {
      "id": "https://example.org/iiif/book1.pdf",
      "type": "Text",
      "label": { "en": [ "Download as PDF" ] },
      "format": "application/pdf"
    }
  ],
  "partOf": [
    {
      "id": "https://example.org/collections/books/",
      "type": "Collection"
    }
  ],
  "start": {
    "id": "https://example.org/iiif/book1/canvas/p2",
    "type": "Canvas"
  },

  // List of Canvases
  "items": [
    {
      "id": "https://example.org/iiif/book1/canvas/p1",
      "type": "Canvas",
      "label": { "@none": [ "p. 1" ] }
      // ...
    }
  ],

  // structure of the resource, described with Ranges
  "structures": [
    {
      "id": "https://example.org/iiif/book1/range/top",
      "type": "Range"
      // Ranges members should be included here
    }
    // Any additional top level Ranges can be included here
  ],

  // Commentary Annotations on the Manifest
  "annotations": [
    {
      "id": "https://example.org/iiif/book1/annotations/p1",
      "type": "AnnotationPage",
      "items": [
        // Annotations about the Manifest are included here
      ]
    }
  ]
}
"""

class Manifest(models.Model):
    DIRECTIONS = (
        ('left-to-right', 'Left to Right'),
        ('right-to-left', 'Right to Left')
    )
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pid = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    summary = models.TextField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    pdf = models.URLField()
    metadata = JSONField(default=dict, blank=False)
    viewingDirection = models.CharField(max_length=13, choices=DIRECTIONS, default="left-to-right")
