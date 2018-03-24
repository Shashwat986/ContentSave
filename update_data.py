import logging
import hashlib
from urllib.parse import urlparse
from model import redis_client
from model import Url, UrlIndex

def check_link_exists(url):
  q = Url.select().where(Url.url == url)

  # If an entry exists
  if len(q) > 0:
    m = q[0]
    return True, m.rowid
  return False, None

def update_content(link_object):
  logging.info("Updating SQLite entry for {}".format(link_object['url']))

  exists, rowid = check_link_exists(link_object['url'])
  if exists:
    Url.update(
      visit_count = Url.visit_count + 1,
      last_visit_time = link_object['datetime']
    ).where(Url.url == link_object['url']).execute()
  else:
    m = Url.create(
      url = url,
      domain = urlparse(url).netloc,
      visit_count = 1,
      last_visit_time = link_object['datetime']
    )

    rowid = m.rowid

  return (not exists), rowid

def update_tfidf(html_object, rowid):
  logging.info("Updating TF-IDF values in Redis")

  doc = html_object['body']

  #url = html_object['url']
  #redis_client.hset("url:hash", rowid, url)

  for word in doc.split():
    pipe = redis_client.pipeline()
    pipe.zincrby("doc:{}".format(rowid), word, 1)
    pipe.zincrby("doc:all", word, 1)
    pipe.execute()

  return True

def update_url_index(html_object, rowid):
  logging.info("Updating SQLite Index entry for row {}".format(rowid))

  m = UrlIndex.select().where(UrlIndex.rowid == rowid).first()
  if m is None:
    UrlIndex.create(
      rowid=rowid,
      title=html_object['title'],
      description=html_object['meta:description'],
      keywords=html_object['meta:keywords'],
      body=html_object['body']
    )
  else:
    UrlIndex.update(
      title=html_object['title'],
      description=html_object['meta:description'],
      keywords=html_object['meta:keywords'],
      body=html_object['body']
    ).where(UrlIndex.rowid == rowid).execute()

  return True

def update_es(html_object, rowid):
  pass

def update_databases(html_object, link_object, force=False):
  if html_object is None:
    return False

  new_element, rowid = update_content(link_object)

  if not new_element and not force:
    logging.info("Entry has already been indexed. Incremented count. Not re-indexing.")
    return False

  update_url_index(html_object, rowid)
  update_es(html_object, rowid)
  update_tfidf(html_object, rowid)

def calculate_tfidf(url):
  try:
    rowid = Url.select().where(Url.url == url)[0].rowid
  except IndexError:
    logging.warning("No entry exists for {}".format(url))
    return {}

  tfidf = {}
  for word, score in redis_client.zrevrange("doc:{}".format(rowid), 0, 99, withscores=True):
    doc_score = redis_client.zscore("doc:all", word)
    if doc_score is None:
      logging.error("There seems to be no score for the word {}".format(word))
    else:
      doc_score = float(doc_score)

    if doc_score == 0:
      logging.error("Why is there a 0 score for the word {}?".format(word))
    else:
      tfidf[word] = float(score) / doc_score

  return tfidf

