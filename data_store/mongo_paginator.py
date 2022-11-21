__author__ = 'mstacy'
import json
import math
import collections
import logging
from bson.objectid import ObjectId
from bson.code import Code
from operator import itemgetter

from collections import OrderedDict
from rest_framework.templatetags.rest_framework import replace_query_param
from pymongo import MongoClient

logger = logging.getLogger(__name__)


def MongoDistinct(field,DB_MongoClient, database, collection, query=None):
    if len(field.split(',')) > 1:
        group = {}
        for itm in field.split(','):
            group[itm.replace('.', '---')] = "${0}".format(itm)
        aggregate = [{"$group": {"_id": group}}]
        iresult = MongoAggregate(
            json.dumps(aggregate), DB_MongoClient, database, collection, query=query)
        result = []
        for itm in iresult:
            temp = itm['_id']
            trans = {}
            for k, v in temp.items():
                trans[k.replace('---', '.')] = v
            result.append(trans)
        return result
    db = DB_MongoClient
    if query:
        try:
            query = json.loads(query)
        except:
            raise Exception("Query: JSON object could be decoded")
        return db[database][collection].find(**query).distinct(field)
    return db[database][collection].distinct(field)

def MongoAggregate(aggregate, DB_MongoClient, database, collection, query=None):
    match = None
    if query:
        try:
            query = json.loads(query)
            query["$match"] = query['filter']
            del query['filter']
        except:
            raise Exception("Query: JSON object could be decoded")
    try:
        aggregate = json.loads(aggregate)
        if query:
            aggregate.insert_one(0, query)
    except:
        raise Exception("Aggregate: JSON object could be decoded")

    db = DB_MongoClient[database][collection]
    results = db.aggregate(aggregate)
    return results

def MongoGroupby(variable,groupby,DB_MongoClient, database, collection, query=None):
    # Deprecated: Please use the new MongoAggregate
    if query:
        try:
            query = json.loads(query)
        except:
            raise Exception("Query: JSON object could be decoded")
    db = DB_MongoClient[database][collection]
    reducer = Code(" function(obj,prev) {prev.Sum += obj.%s;prev.count+=1; prev.Avg = prev.Sum/prev.count;}" % (variable))
    # FIXME: group is replaced by aggregate - https://www.mongodb.com/docs/upcoming/reference/operator/aggregation/group/
    results = db.group(groupby,query,{'Sum':0,'Avg':0,'count':0,'Variable':variable},reducer)
    data_out=[]
    try:
        data_out = multikeysort(results, groupby)
    except:
        data_out=results
    return data_out

def multikeysort(self,items, columns):
    comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]
    def comparer(left, right):
        for fn, mult in comparers:
            result = cmp(fn(left), fn(right))
            if result:
                return mult * result
            else:
                return 0
    return sorted(items, cmp=comparer)

def set_pagination_vars(count,page,nPerPage):
    if nPerPage == 0:
        page=1
        offset=0
        max_page=1
    else:
        max_page = math.ceil(float(count) / nPerPage)
        # Page min is 1
        if page < 1:
            page = 1
        #Change page to last page with data
        if page * nPerPage > count:
            page = int(max_page)
        #Cover count =0
        if page < 1:
            page = 1
        offset = (page - 1) * nPerPage
    return page,offset,max_page
def set_next_prev_urls(page,max_page,uri):
    if page < max_page:
        nexturi = replace_query_param(uri, 'page', page + 1)
    else:
        nexturi = None
    if page > 1:
        previous = replace_query_param(uri, 'page', page - 1)
    else:
        previous = None
    return nexturi, previous
def MongoDataPagination(DB_MongoClient, database, collection, query=None, page=1, nPerPage=None, uri=''):
    db = DB_MongoClient
    if query:
        try:
            query = json.loads(query)
        except:
            raise Exception("Query: JSON object could be decoded")

        count = db[database][collection].count_documents(**query)
        #set page variables
        page,offset,max_page = set_pagination_vars(count,page,nPerPage)
        #Data
        data = [row for row in db[database][collection].find(**query).skip(offset).limit(nPerPage)]
    else:
        count = db[database][collection].estimated_document_count()
        #set page variables
        page,offset,max_page = set_pagination_vars(count,page,nPerPage)
        #Data
        data = [row for row in db[database][collection].find().skip(offset).limit(nPerPage)]
    nexturi, previous=set_next_prev_urls(page,max_page,uri)

    result = {'count': count, 'meta': {'page': page, 'page_size': nPerPage, 'pages': int(max_page)}, 'next': nexturi,
              'previous': previous, 'results': data}
    #keep sort order
    try:
        od = collections.OrderedDict(sorted(result.items()))
    except:
        # older python versions < 2.7
        od = OrderedDict(sorted(result.items()))
    return od

# FIXME: combine update and insert to handle one or many records and with or without _id
def MongoDataInsert(DB_MongoClient, database, collection,data):
    db = DB_MongoClient
    #Update if data already in collection
    # if '_id' in data:
    #     id=data['_id']
    #     return MongoDataSave(DB_MongoClient, database, collection,id,data)
    #return db[database][collection].insert_one(data)
    if type(data) == type([]):
        #print(dir(db[database][collection]))
        return db[database][collection].insert_many(data)
    else:
        return db[database][collection].insert_one(data)

def MongoDataUpdate(DB_MongoClient: MongoClient, database: str, collection: str, data: dict) -> str:
    _id = data.get("_id")
    if _id and isinstance(_id, ObjectId):
        DB_MongoClient[database][collection].update_one({"_id": _id}, {"$set": data})
        return str(_id)

def MongoDataGet(DB_MongoClient, database, collection,id):
    db = DB_MongoClient
    term_id=get_id(id)
    data = db[database][collection].find_one({'_id':term_id})
    if not data:
        data = {"Error":"DATA RECORD NOT FOUND"}
    return data

def MongoDataDelete(DB_MongoClient, database, collection,id):
    db = DB_MongoClient
    term_id=get_id(id)
    result= db[database][collection].delete_one({'_id':term_id})
    if result.deleted_count:
        return result
    else:
        return {"Error":"UNABLE TO DELETE: DATA RECORD NOT FOUND"}

def MongoDataSave(DB_MongoClient, database, collection,id,data):
    data["_id"] = ObjectId(id) if not data.get("_id") else ObjectId(data["_id"])
    return MongoDataUpdate(DB_MongoClient, database, collection, data)

def is_number(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return True

def get_id(id):
    if is_number(id):
        if '.' in id:
            result=float(id)
        else:
            result=int(id)
    else:
        try:
            result=ObjectId(id)
        except:
            result = id
    return result
