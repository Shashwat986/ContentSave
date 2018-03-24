import logging
import redis
from redis.exceptions import ConnectionError
from peewee import Model, CharField, DateTimeField, IntegerField
from playhouse.sqlite_ext import SqliteExtDatabase, FTSModel, RowIDField, SearchField

redis_client = redis.StrictRedis(host='localhost', port=6381, db=0)

sqlite_db = SqliteExtDatabase('db/sqlite.db')

def test_connections():
  try:
    redis_client.ping()
  except ConnectionError:
    logging.exception("Redis connection failed")
    return False

  # TODO

  return True

class Url(Model):
  class Meta:
    database = sqlite_db

  rowid = RowIDField()
  url = CharField()
  domain = CharField()
  visit_count = IntegerField()
  last_visit_time = DateTimeField()

class UrlIndex(FTSModel):
  class Meta:
    database = sqlite_db
    options = {"tokenize" : "porter"}

  rowid = RowIDField()
  title = SearchField()
  description = SearchField()
  keywords = SearchField()
  body = SearchField()

def insert_url(url, **kwargs):
  pass
