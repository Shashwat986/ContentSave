from model import redis_client
from model import Url
from peewee import fn

def get_metadata():
  print ("Total URLs processed:", Url.select().count())
  print ("Vocabulary Size:", redis_client.zcard('doc:all'))

  freq_domains = list(
    map(
      lambda x: x.domain,
      Url.select(
        Url.domain,
        fn.SUM(Url.visit_count).alias('sc')
      ).group_by(Url.domain)
      .order_by(-fn.SUM(Url.visit_count))
      [0:4]
    )
  )

  print ("Most frequent domains:", ", ".join(freq_domains))
