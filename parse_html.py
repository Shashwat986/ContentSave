import hashlib
from urllib.parse import urlparse
from model import redis_client
from model import Url, UrlIndex

def update_content(link_object):
  url = link_object['url']
  q = Url.select().where(Url.url == url)

  # If an entry exists
  if len(q) > 0:
    # FIXME: http://docs.peewee-orm.com/en/latest/peewee/querying.html#atomic-updates
    m = q[0]
    m.visit_count += 1
    m.last_visit_time = link_object['datetime']
    m.save()
    return False, m.rowid

  m = Url.create(
    url=url,
    domain=urlparse(url).netloc,
    visit_count=1,
    last_visit_time=link_object['datetime']
  )

  return True, m.rowid

def update_tfidf(html_object, rowid):
  doc = html_object['body']

  #url = html_object['url']
  #redis_client.hset("url:hash", rowid, url)

  for word in doc.split():
    pipe = redis_client.pipeline()
    pipe.zincrby("doc:{}".format(rowid), word, 1)
    pipe.zincrby("doc:all", word, 1)
    pipe.execute()

  return True

def update_databases(html_object, link_object):
  new_element, rowid = update_content(link_object)

  if not new_element: return False

  return update_tfidf(html_object, rowid)

def calculate_tfidf(url):
  try:
    rowid = Url.select().where(Url.url == url)[0].rowid
  except IndexError:
    return {}

  tfidf = {}
  for word, score in redis_client.zrevrange("doc:{}".format(rowid), 0, 99, withscores=True):
    doc_score = redis_client.zscore("doc:all", word)
    if doc_score is None:
      raise Exception("Something went wrong")
    else:
      doc_score = float(doc_score)

    if doc_score == 0:
      raise Exception("Something went wrong")

    tfidf[word] = float(score) / doc_score

  return tfidf

