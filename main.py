import logging
from read_chrome import get_links
from fetch_html import get_headless_html
from parse_html import update_databases, calculate_tfidf
from metadata import get_metadata
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
    logging.info("Fetching {}".format(link['url']))
    url_object = get_headless_html(link['url'])

    logging.debug("Updating DB Values")
    update_databases(url_object, link)

    redis_client.set('last_fetch_time', link['time'])
    count += 1
    logging.info("{:>5} processed so far".format(count), end="\r")

  return count

def fetch_tfidf(url):
  print (sorted(calculate_tfidf(url).items(), key=lambda x: -x[1])[0:50])

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  #fetch_tfidf("http://docs.peewee-orm.com/en/latest/peewee/models.html")
  fetch_and_parse_links(40)
  get_metadata()
