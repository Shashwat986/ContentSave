from read_chrome import get_links, from_google_time
from fetch_html import get_headless_html
from model import redis_client

fetched = redis_client.get('last_fetch_time')

if fetched:
  try:
    fetched = float(fetched)
  except ValueError:
    fetched = None

last_fetch_time = fetched
for link in get_links(fetched):
  last_fetch_time = link['time']

redis_client.set('last_fetch_time', last_fetch_time)
