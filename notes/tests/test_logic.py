from django.test import Client, TestCase
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.utils import IntegrityError
from pytils.translit import slugify

from notes.models import Note


User = get_user_model()


class TestNotesCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author')
        cls.user = User.objects.create(username='reader')
        cls.note = Note.objects.create(
            title='Test',
            text='test_text',
            author=cls.author,
            slug='test_slug',
        )
        cls.auth_author = Client()
        cls.auth_reader = Client()
        cls.auth_author.force_login(cls.author)
        cls.auth_reader.force_login(cls.user)
        cls.form_data = {
            'title': 'test_title',
            'text': 'test_text',
            'slug': 'slug',
            'author': cls.author,
        }
        cls.form_data_without_slug = {
            'title': 'test_title',
            'text': 'test_text',
            'author': cls.author,
        }
        cls.form_data_edit = {
            'title': 'updated_title',
            'text': 'test_text',
            'slug': 'slug',
        }
        cls.url_add = reverse('notes:add')
        cls.url_delete = reverse('notes:delete', args=(cls.note.slug,))
        cls.url_edit = reverse('notes:edit', args=(cls.note.slug,))
        cls.url_done = reverse('notes:success')

    def test_anonim_cant_create_notes(self):
        """Аноним не может создавать заметки."""
        self.client.post(self.url_add, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_reader_cant_delete_edit_notes_of_other_user(self):
        """нельзя воздействовать на чужие заметки."""
        response = self.auth_reader.delete(self.url_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        response = self.auth_reader.post(self.url_edit, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_author_can_delete_notes(self):
        """Автор может удалять свои заметки."""
        response = self.auth_author.delete(self.url_delete)
        self.assertRedirects(response, self.url_done)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_author_can_edit_notes(self):
        """Автор может редактировать свои заметки."""
        response = self.auth_author.post(self.url_edit, self.form_data_edit)
        self.assertRedirects(response, self.url_done)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, 'updated_title')

    def test_authorised_user_can_create_notes(self):
        """Авторизованый пользователь может создавать заметки."""
        response = self.auth_author.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, f'{self.url_done}')
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        note = Note.objects.get(slug='slug')
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])

    def test_uniq_slug(self):
        """Нельзя создать две заметки с одинаковым слагом."""
        with self.assertRaises(IntegrityError):
            self.another_note = Note.objects.create(
                title='test_title',
                text='test_text',
                author=self.author,
                slug='test_slug'
            )

    def test_empty_slug(self):
        """Слаг будет в любом случае."""
        response = self.auth_author.post(self.url_add, data=self.form_data_without_slug)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertAlmostEqual(Note.objects.count(), 2)
        new_note = Note.objects.get(id=2)
        expected_slug = slugify(self.form_data_without_slug['title'])
        self.assertEqual(new_note.slug, expected_slug)
