from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Topic, User, Board, Post
from django.views import generic
from .forms import NewTopicForm


class IndexView(generic.ListView):
    template_name = 'forum/index.html'
    context_object_name = 'boards'
    model = Board


class BoardTopicsView(generic.DetailView):
    model = Board
    template_name = 'forum/topics.html'
    context_object_name = 'board'


def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)
    user = User.objects.first()  # TODO: get the currently logged in user

    if request.method == 'POST':
        form = NewTopicForm(request.POST)

        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = user
            topic.save()
            post = Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=user
            )
            return redirect('forum:board_topics', pk=board.pk)  # TODO: redirect to the created topic page
    else:
        form = NewTopicForm()
    return render(request, 'forum/new_topic.html', {'board': board, 'form': form})
