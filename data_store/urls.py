__author__ = 'mstacy'
from django.urls import include, path, re_path
from django.conf.urls import  url
from data_store.views import MongoDataStore, DataStore, DataStoreDetail
#from rest_framework.urlpatterns import format_suffix_patterns
from api import config

urlpatterns = [
    path('data/', MongoDataStore.as_view(), name='data-list'),
    re_path(r'data/(?P<database>[^/]+)/$', MongoDataStore.as_view(), name='data-list'),
    re_path(r'data/(?P<database>[^/]+)/(?P<collection>[^/]+)/$', DataStore.as_view(),name='data-detail'),
    re_path(r'data/(?P<database>[^/]+)/(?P<collection>[^/]+)/(?P<id>[^/]+)/$', DataStoreDetail.as_view(),
                           name='data-detail-id'),
]


#urlpatterns = format_suffix_patterns(urlpatterns, allowed=['api', 'json', 'jsonp', 'xml', 'yaml'])
