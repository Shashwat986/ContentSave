from model import redis_client
from model import Url
from peewee import fn

def get_metadata():
  print ("Total URLs processed:", Url.select().count())
  print ("Vocabulary Size:", redis_client.zcard('doc:all'))

  #freq_domains = Url.select(fn.Sum(

  #print ("Most frequent domains:", Url.select(
