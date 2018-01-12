import django.urls
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Topic, User, Board, Post
from django.db.models import Count, F
from django.views import generic
from .forms import NewTopicForm, PostForm
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


class BoardListView(generic.ListView):
    template_name = 'forum/index.html'
    context_object_name = 'boards'
    model = Board


class TopicListView(generic.ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'forum/topics.html'
    paginate_by = 20

    def get_queryset(self):
        self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
        queryset = self.board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
        return queryset

    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board
        return super().get_context_data(**kwargs)


# @method_decorator(login_required, 'dispatch')
# class TopicCreateView(generic.CreateView):
#     model = Topic
#     form_class = NewTopicForm
#     template_name = 'forum/new_topic.html'
#     context_object_name = 'board'
#     # pk_url_kwarg = 'pk' #
#
#
#     def form_valid(self, form):
#         topic = form.save(commit=False)
#         topic.board = self.request.board
#         topic.starter = self.request.user
#         topic.save()
#         post = Post.objects.create(
#             message=form.cleaned_data.get('message'),
#             topic=topic,
#             created_by=self.request.user
#         )
#         return redirect('forum:topic_posts', pk=self.request.board.pk, topic_pk=topic.pk)
#
#     def get_queryset(self):
#         return Board.objects.get(self.kwargs.get('pk'))


@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)

        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.save()
            post = Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=request.user
            )
            return redirect('forum:topic_posts', pk=board.pk, topic_pk=topic.pk)
    else:
        form = NewTopicForm()
    return render(request, 'forum/new_topic.html', {'board': board, 'form': form})


class PostListView(generic.ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'forum/topic_posts.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        session_key = 'viewed_topic_{}'.format(self.topic.pk)
        if not self.request.session.get(session_key, False):
            self.topic.views = F('views') + 1
            self.topic.save()
            self.request.session[session_key] = True
        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(Topic, board__pk=self.kwargs.get('pk'), pk=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('created_at')
        return queryset


def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    topic.views = F('views') + 1
    topic.save()
    return render(request, 'forum/topic_posts.html', {'topic': topic})


@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            topic.last_updated = timezone.now()
            topic.save()

            topic_url = django.urls.reverse('forum:topic_posts', kwargs={'pk': pk, 'topic_pk': topic_pk})
            topic_post_url = f'{topic_url}?page={topic.get_page_count()}#{post.pk}'
            return redirect(topic_post_url)
    else:
        form = PostForm()
    return render(request, 'forum/reply_topic.html', {'topic': topic, 'form': form})


@method_decorator(login_required, 'dispatch')
class PostUpdateView(generic.UpdateView):
    model = Post
    fields = ('message',)
    template_name = 'forum/edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        topic_url = django.urls.reverse('forum:topic_posts', kwargs={'pk': post.topic.board.pk, 'topic_pk': post.topic.pk})
        topic_post_url = f'{topic_url}?page={post.topic.get_page_count()}#{post.pk}'
        return redirect(topic_post_url)

        # return redirect('forum:topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)
