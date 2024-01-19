from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.utils import IntegrityError

import unittest

from datetime import datetime, timedelta

from notes.models import Note

User = get_user_model()


class TestNotes(TestCase):
    """Не авторизованному пользователю не доступна форма создания."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author')
        cls.note = Note.objects.create(
            title='test_title',
            text='test_text',
            author=cls.author
        )  # Создали новость без слага.
        cls.note_slug = Note.objects.create(
            title='test',
            text='test',
            author=cls.author,
            slug='test'
        )

    def test_note_has_slug_anyway(self):
        self.assertTrue(self.note.slug)

    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        # Авторизуем клиент при помощи ранее созданного пользователя.
        urls_args = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for url, arg in urls_args:
            with self.subTest(url=url):
                addres = reverse(url, args=arg)
                response = self.client.get(addres)
                self.assertIn('form', response.context)

    def test_uniq_slug(self):
        with self.assertRaises(IntegrityError):
            self.another_note = Note.objects.create(
                title='test_title',
                text='test_text',
                author=self.author,
                slug='test'
            )
