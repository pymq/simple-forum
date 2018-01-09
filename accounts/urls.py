from django.conf.urls import url
from . import views
# from accounts import views


app_name = 'accounts'
urlpatterns = [
    url(r'signup/', views.signup, name='signup'),
]
