from django.test import TestCase
from bson import ObjectId

from data_store.mongo_paginator import get_id

class MongoPaginatorTest(TestCase):

    def test_get_id(self):
        self.assertEqual(get_id('123'), 123)
        self.assertEqual(get_id('123.0'), 123.0)
        self.assertEqual(get_id('123.0'), 123)
        self.assertEqual(get_id('test'), 'test')
        self.assertEqual(get_id('test.other'), 'test.other')


    def test_get_id_object_id(self):
        self.assertEqual(get_id(ObjectId('a'*24)), ObjectId('a'*24))


    def test_get_id_numerical_input(self):
        self.assertRaises(TypeError, get_id, 123)
        self.assertRaises(TypeError, get_id, 123.0)
