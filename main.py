from read_chrome import get_links, from_google_time
from fetch_html import get_headless_html
from parse_html import *
from model import redis_client

def fetch_and_parse_links(limit=5):
  fetched = redis_client.get('last_fetch_time')

  if fetched:
    try:
      fetched = float(fetched)
    except ValueError:
      fetched = None

  count = 0
  for link in get_links(fetched, limit):
    print ("--- Fetching {}".format(link['url']))
    html = get_headless_html(link['url'])
    print ("--- Updating TF-IDF Values")
    update_tfidf(html, link['url'])
    redis_client.set('last_fetch_time', link['time'])
    count += 1

  return count

def fetch_tfidf(url):
  print (sorted(calculate_tfidf(url).items(), key=lambda x: -x[1])[0:50])

def get_metadata():
  print ("Total URLs processed:", redis_client.hlen('url:hash'))
  print ("Vocabulary Size:", redis_client.zcard('doc:all'))
  print ("Most frequent domains:", ", ".join(map(lambda x: x.decode('ascii'), redis_client.zrevrange("url:domain", 0, 4))))

if __name__ == "__main__":
  #fetch_tfidf("http://docs.peewee-orm.com/en/latest/peewee/models.html")
  fetch_and_parse_links(16)
  get_metadata()
