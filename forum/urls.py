from django.conf.urls import url
from . import views

app_name = 'forum'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^boards/(?P<pk>\d+)/$', views.BoardTopicsView.as_view(), name='board_topics'),
    url(r'^boards/(?P<pk>\d+)/new/$', views.new_topic, name='new_topic'),
]
