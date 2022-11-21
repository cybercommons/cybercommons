_author__ = 'mstacy'
from django.urls import include, path, re_path

from catalog.views import Catalog,CatalogData, CatalogDataDetail # SourceList, SourceDetail

#from rest_framework.urlpatterns import format_suffix_patterns
#from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
     path('data/', Catalog.as_view(),name='catalog-list'),
     re_path(r'data/(?P<database>[^/]+)/$',Catalog.as_view(),name='catalog-list'),
     re_path(r'data/(?P<database>[^/]+)/(?P<collection>[^/]+)/$',CatalogData.as_view(),name='catalog-detail'),
     re_path(r'data/(?P<database>[^/]+)/(?P<collection>[^/]+)/(?P<id>[^/]+)/$', CatalogDataDetail.as_view(),
             name='catalog-detail-id'),
]

#urlpatterns = format_suffix_patterns(urlpatterns, allowed=['api', 'json', 'jsonp', 'xml', 'yaml'])
