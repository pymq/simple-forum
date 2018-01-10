from django.test import TestCase
from django.core.urlresolvers import reverse
from django.urls import resolve
from forum.models import Board


class IndexViewTests(TestCase):
    def setUp(self):
        self.board = Board.objects.create(name='Django', description='Django board.')
        url = reverse('forum:index')
        self.response = self.client.get(url)

    def test_index_view_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_index_url_resolves_index_view(self):
        view = resolve('/')
        self.assertEquals(view.view_name, 'forum:index')

    def test_index_view_contains_link_to_topics_page(self):
        board_topics_url = reverse('forum:board_topics', kwargs={'pk': self.board.pk})
        self.assertContains(self.response, 'href="{0}"'.format(board_topics_url))