# -*- coding: utf-8 -*-

from django.http import HttpRequest
from django.test import TestCase
from utils.query import get_text_tokenizer

class TestStringTokenizerCase(TestCase):
    """ Tokenizer Test """

    def test_tokenizer_test(self):
        text = "This is a test -This -is -NOT -a -test"
        includes, excludes = get_text_tokenizer(text)
        self.assertEquals('-'.join(includes), "This-is-a-test")
        self.assertEquals('-'.join(excludes), "This-is-NOT-a-test")
