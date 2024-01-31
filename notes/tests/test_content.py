from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNotes(TestCase):
    """Не авторизованному пользователю не доступна форма создания."""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:list')
        cls.url_add = reverse('notes:add')
        cls.author = User.objects.create(username='Автор')
        cls.user = User.objects.create(username='User')
        cls.note = Note.objects.create(
            title='test_title',
            text='test_text',
            author=cls.author
        )
        cls.url_edit = reverse('notes:edit', args=(cls.note.slug,))

    def test_note_in_list_for_author(self):
        """Заметка передаётся в контексте для автора."""
        self.client.force_login(self.author)
        response = self.client.get(self.url)
        object_list = response.context['object_list']
        assert self.note in object_list

    def test_note_not_in_list_for_another_user(self):
        """Заметка не передаётся в контексте если не автор."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        object_list = response.context['object_list']
        assert self.note not in object_list

    def test_create_note_page_contains_form(self):
        """Страница создания заметки содержит форму."""
        self.client.force_login(self.author)
        response = self.client.get(self.url_add)
        assert 'form' in response.context
        assert isinstance(response.context['form'], NoteForm)

    def test_edit_note_page_contains_form(self):
        """Страница редактирования заметки содержит форму."""
        self.client.force_login(self.author)
        response = self.client.get(self.url_edit)
        assert 'form' in response.context
        assert isinstance(response.context['form'], NoteForm)
