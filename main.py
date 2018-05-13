import logging
from read_chrome import get_bookmarks, get_links, get_feedly
from fetch_html import get_headless_html, Status
from update_data import update_databases, calculate_tfidf, check_link_exists
from search import get_metadata
from model import redis_client, test_connections

type_map = {
  'history': {
    'redis_key': 'last_fetch_time',
    'method': 'get_links'
  },
  'bookmark': {
    'redis_key': 'last_bookmark_fetch_time',
    'method': 'get_bookmarks'
  },
  'feedly': {
    'redis_key': 'last_feedly_fetch_time',
    'method': 'get_feedly'
  }
}

def fetch_and_parse_links(limit = 5, force = False, fetch_type = "history"):
  fetch_metadata = type_map[fetch_type]
  fetched = redis_client.get(fetch_metadata['redis_key'])

  if fetched:
    try:
      fetched = float(fetched)
    except ValueError:
      fetched = None

  count = 0
  for link in eval(fetch_metadata['method'])(fetched, limit):
    logging.info("Fetching {}".format(link['url']))

    exists, _ = check_link_exists(link['url'])

    # If we don't have an entry for this URL right now
    if exists and not force:
      logging.info("Already fetched. Not fetching again")
    else:
      url_object = get_headless_html(link['url'])

      if type(url_object) == Status:
        if url_object.status == Status.NO_CONNECTION:
          logging.error("No Internet connection")
          return count

        logging.info("Unable to fetch URL data. Ignoring this URL")
      else:
        logging.debug("Updating DB Values")
        update_databases(url_object, link, force, True)

    redis_client.set(fetch_metadata['redis_key'], link['time'])

    count += 1

    print("{:>5} processed so far".format(count))

  return count

def fetch_tfidf(url):
  print (sorted(calculate_tfidf(url=url).items(), key=lambda x: -x[1])[0:50])

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)

  if not test_connections():
    logging.error("Connection issues")
    exit(1)

  #fetch_tfidf("http://docs.peewee-orm.com/en/latest/peewee/models.html")
  count = fetch_and_parse_links(10000, fetch_type="feedly")
  print ("URLs Processed: ", count)
  #get_metadata()
