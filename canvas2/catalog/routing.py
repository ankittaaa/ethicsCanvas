from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'ws/canvas/(?P<pk>\d+)/trial-idea/$', consumers.TrialIdeaConsumer),
    url(r'ws/project/(?P<pk>\d+)/idea/$', consumers.IdeaConsumer),
    url(r'ws/canvas/(?P<pk>\d+)/comment/$', consumers.CommentConsumer),
    url(r'ws/project/(?P<pk>\d+)/collab/$', consumers.CollabConsumer),
    url(r'ws/project/(?P<pk>\d+)/tag/$', consumers.TagConsumer),
]
