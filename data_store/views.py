# from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework.exceptions import APIException, ValidationError
#from pymongo import MongoClient
from api import config
from .models import dataStore
# Create your views here.
from rest_framework.settings import api_settings
from .mongo_paginator import MongoDataPagination, MongoDataUpdate, MongoDistinct,MongoGroupby, MongoDataGet,MongoDataDelete,MongoDataSave,MongoDataInsert, MongoAggregate
from .renderer import DataBrowsableAPIRenderer, mongoJSONPRenderer,mongoJSONRenderer
from rest_framework_xml.renderers import XMLRenderer
from rest_framework_yaml.renderers import YAMLRenderer
#from rest_framework.renderers import XMLRenderer, YAMLRenderer,JSONPRenderer
from rest_framework.parsers import JSONParser
from .permission import  DataStorePermission, createDataStorePermission
from celery import Celery
from bson import ObjectId
from bson.errors import InvalidId


class celeryConfig:
    BROKER_URL = config.BROKER_URL
    BROKER_USE_SSL = config.BROKER_USE_SSL
    CELERY_SEND_EVENTS = True
    CELERY_TASK_RESULT_EXPIRES = None
    CELERY_RESULT_BACKEND = config.CELERY_RESULT_BACKEND
    CELERY_MONGODB_BACKEND_SETTINGS = config.CELERY_MONGODB_BACKEND_SETTINGS


app = Celery()
app.config_from_object(celeryConfig)


class MongoDataStore(APIView):
    permission_classes = ( createDataStorePermission,)
    renderer_classes = (DataBrowsableAPIRenderer, mongoJSONRenderer, mongoJSONPRenderer, XMLRenderer, YAMLRenderer)
    title = "Database"
    parser_classes = (JSONParser,)
    connect_uri = config.DATA_STORE_MONGO_URI
    view_reverse='data'
    name = "Data Store"
    exclude= config.DATA_STORE_EXCLUDE
    def __init__(self):
        #self.db = MongoClient(host=self.connect_uri)
        self.db = app.backend.database.client
    def get(self, request, database=None, format=None):
        urls = []
        if database:
            self.title = "Collection"
            data = list(self.db[database].list_collection_names())
            data.sort()
            for col in data:
                if "%s.%s" % (database, col) in self.exclude or col in self.exclude:
                    pass
                else:
                    urls.append(reverse("%s-detail" % (self.view_reverse),
                                        kwargs={'database': database, 'collection': col}, request=request))
            return Response({'Database': database, 'Available Collections': urls})
        else:
            self.title = "Database"
            # This section used for catalog django app
            if self.name == "Catalog":
                data = self.include
            else:
                data = list(self.db.list_database_names())
                data.sort()

            for db in data:
                if db in self.exclude:
                    pass
                else:
                    urls.append(reverse("%s-list" % (self.view_reverse),
                                        kwargs={'database': db}, request=request))
            return Response({
                'Available Databases': urls})

    def post(self, request, database=None, format=None):
        # Action Delete
        action = request.data.get('action', '')
        collection = request.data.get('collection', None)

        if action.lower() == 'delete':
            if collection and database:
                try:
                    self.db[database].drop_collection(collection)
                    return Response({collection: "Deleted"})
                except Exception as e:
                    return Response({"Error": str(e)})
            elif not database and request.data.get('database', None):
                database = request.data.get('database', None)
                try:
                    self.db.drop_database(database)
                    return Response({database: "Deleted"})
                except Exception as e:
                    return Response({"Error": str(e)})
            else:
                return Response({"ERROR": "Database {0} Collection {1} Action {2}".format(database, collection, action)})
        # Action Create (default None)
        if database:
            col = request.data.get('collection', None)
            if col:
                data = request.data.get('data', {})
                if self.db[database][col].estimated_document_count() == 0:
                    self.db[database][col].insert_one(data)
                    if not data:
                        self.db[database][col].delete_one({})
                    return Response({'database': database, 'collection': col})
                return Response({'ERROR': f'Collection already exists'})
            else:
                return Response({'ERROR': "Must submit 'collection' name as part of post"})
        else:
            data = request.data.get('database', None)
            if data:
                self.db[data]['default_collection'].insert_one({})
                return Response({'database': data})
            else:
                return Response({'ERROR': "Must submit 'database' name as part of post"})


class DataStore(APIView):
    permission_classes = (DataStorePermission,) #DjangoModelPermissionsOrAnonReadOnly,)
    model = dataStore 
    renderer_classes = (DataBrowsableAPIRenderer, mongoJSONRenderer, mongoJSONPRenderer, XMLRenderer, YAMLRenderer)
    parser_classes = (JSONParser,)
    connect_uri = config.DATA_STORE_MONGO_URI
    def __init__(self):
        #self.db = MongoClient(host=self.connect_uri)
        self.db = app.backend.database.client

    def get(self, request, database=None, collection=None, format=None):
        query = request.query_params.get('query', None)
        page_size = request.query_params.get(api_settings.user_settings.get('PAGINATE_BY_PARAM', 'page_size'),
                                             api_settings.user_settings.get('PAGINATE_BY', 10))
        try:
            page = int(request.query_params.get('page', 1))
        except:
            page = 1
        try:
            page_size = int(page_size)
        except:
            page_size = int(api_settings.user_settings.get('PAGINATE_BY', 10))

        url = request and request.build_absolute_uri() or ''

        # set new variables for aggregation and distinct
        distinct = request.query_params.get('distinct', None)
        aggregate = request.query_params.get('aggregate', None)

        if distinct:
            data = MongoDistinct(
                distinct, self.db, database, collection, query=query)
        elif aggregate:
            data = None
            # Currently do not want to have aggregation activity create new collection.
            # This could also change documents within collection out to existing data collection.
            restricted_actions = ['$out', '$merge']
            for item in restricted_actions:
                if item in aggregate:
                    data = {"Error": "{0} is not allowed restrict write operations with database.".format(
                        ",".join(restricted_actions))}
            if not data:
                data = MongoAggregate(aggregate, self.db,
                                      database, collection, query=query)
        else:
            data = MongoDataPagination(
                self.db, database, collection, query=query, page=page, nPerPage=page_size, uri=url)
        return Response(data)

    def post(self, request, database=None, collection=None, format=None):
        try:
            data = request.data
            if isinstance(data, list) and any([record.get("_id") for record in data]):  # The underlying upsert functionality does not properly handle multiple items with existing _id fields
                raise ValidationError({"data":"Updating multiple records in a single request is not supported"})
            existing_id = data.get("_id") if type(data) != list else None
            if existing_id:
                try:
                    data["_id"] = existing_id if isinstance(existing_id, ObjectId) else ObjectId(existing_id)
                except InvalidId:
                    raise ValidationError({"data": "Invalid '_id' used, must be 24-character hex string or omit '_id' to create new record","error":"Invalid '_id'"})
                result = MongoDataUpdate(self.db, database, collection, data)
            else:
                result = MongoDataInsert(self.db, database, collection, data)
            return Response(result)
        except Exception as e:
            raise ValidationError({"data":"Error inserting data, If '_id' is within data, please check '_id' duplication.","error":str(e)})

class DataStoreDetail(APIView):
    permission_classes = (DataStorePermission,) #DjangoModelPermissionsOrAnonReadOnly,)
    model = dataStore
    renderer_classes = (DataBrowsableAPIRenderer, mongoJSONRenderer, mongoJSONPRenderer, XMLRenderer, YAMLRenderer)
    parser_classes = (JSONParser,)
    connect_uri = config.DATA_STORE_MONGO_URI
    def __init__(self):
        #self.db = MongoClient(host=self.connect_uri)
        self.db = app.backend.database.client
    def get(self, request, database=None, collection=None, id=None, format=None):
        data = MongoDataGet(self.db, database, collection, id)
        return Response(data)

    def put(self, request, database=None, collection=None, id=None, format=None):
        return Response(MongoDataSave(self.db, database, collection, id, request.data))

    def delete(self, request, database=None, collection=None, id=None, format=None):
        result = MongoDataDelete(self.db, database, collection, id)
        return Response({"deleted_count": result.deleted_count, "_id": id})
