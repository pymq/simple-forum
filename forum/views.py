from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Topic, User, Board, Post
from django.db.models import Count, F
from django.views import generic
from .forms import NewTopicForm, PostForm
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


class IndexView(generic.ListView):
    template_name = 'forum/index.html'
    context_object_name = 'boards'
    model = Board


class BoardTopicsView(generic.DetailView):
    model = Board
    template_name = 'forum/topics.html'
    context_object_name = 'board'


def board_topics(request, pk):
    board = get_object_or_404(Board, pk=pk)
    topics = board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
    return render(request, 'forum/topics.html', {'board': board, 'topics': topics})


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
            return redirect('forum:topic_posts', pk=pk, topic_pk=topic_pk)
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
        return redirect('forum:topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)
