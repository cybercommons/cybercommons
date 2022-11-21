from django.urls import include, path, re_path
#from django.conf.urls import patterns, url
from django.contrib import admin
from cybercom_queue.views import Run, Queue, UserTasks, UserResult,flushMemcache
#from rest_framework.urlpatterns import format_suffix_patterns

admin.autodiscover()

urlpatterns = [
     path('', Queue.as_view(), name="queue-main"),
     re_path(r'run/(?P<task_name>[-\w .]+)/$', Run.as_view(), name='run-main'),
     re_path(r'task/(?P<task_id>[-\w]+)/$', UserResult.as_view(), name='queue-task-result'),
     path('usertasks/', UserTasks.as_view(), name='queue-user-tasks'),
     path(r'memcache',flushMemcache.as_view(), name= 'flush-memcache'),
]

#urlpatterns = format_suffix_patterns(urlpatterns, allowed=['api', 'json', 'jsonp', 'xml', 'yaml'])
