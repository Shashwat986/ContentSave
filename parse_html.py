import hashlib
from urllib.parse import urlparse
from model import redis_client

def update_tfidf(doc, url):
  m = hashlib.md5()
  m.update(url.encode('utf-8'))
  name = m.hexdigest()

  if redis_client.hget("url:hash", name):
    print ("--- {} already updated".format(url))
    return

  pipe = redis_client.pipeline()
  pipe.hset("url:hash", name, url)
  pipe.zincrby("url:domain", urlparse(url).netloc, 1)
  pipe.execute()

  for word in doc.split():
    pipe = redis_client.pipeline()
    pipe.zincrby("doc:{}".format(name), word, 1)
    pipe.zincrby("doc:all", word, 1)
    pipe.execute()

def calculate_tfidf(url):
  m = hashlib.md5()
  m.update(url.encode('utf-8'))
  name = m.hexdigest()

  tfidf = {}
  for word, score in redis_client.zrevrange("doc:{}".format(name), 0, 99, withscores=True):
    doc_score = redis_client.zscore("doc:all", word)
    if doc_score is None:
      raise Exception("Something went wrong")
    else:
      doc_score = float(doc_score)

    tfidf[word] = float(score) / doc_score

  return tfidf

