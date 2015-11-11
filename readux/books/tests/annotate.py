from django.contrib.auth import get_user_model
from django.test import TestCase
import json

from readux.annotations.models import Annotation
from readux.books.annotate import annotation_to_tei
from readux.books import tei

class AnnotatedTei(TestCase):

    def test_annotation_to_tei(self):
        note = Annotation(text="Here's the thing", quote="really",
            extra_data=json.dumps({'sample data': 'foobar'}))

        teinote = annotation_to_tei(note)
        self.assert_(isinstance(teinote, tei.Note))
        self.assertEqual('annotation-%s' % note.id, teinote.id)
        self.assert_(teinote.href.endswith(note.get_absolute_url()))
        self.assertEqual(note.text, teinote.paragraphs[0])

        # annotation user should be set as note response
        user = get_user_model()(username='an_annotator')
        note.user = user
        teinote = annotation_to_tei(note)
        self.assertEqual(user.username, teinote.resp)

        # test that markdown formatting is coming through
        footnote = '''Footnotes[^1] have a label and content.

[^1]: This is some footnote content.'''
        note.text = footnote
        teinote = annotation_to_tei(note)
        self.assert_('<ref target="#fn1" type="noteAnchor">1</ref>' in
            teinote.serialize())


