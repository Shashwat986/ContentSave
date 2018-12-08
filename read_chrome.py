import sqlite3
import os
import sys
import logging
import json
from shutil import copyfile
from datetime import datetime, timedelta
import requests

# Convert from UNIX timestamp to Google's time
def to_google_time(timestamp):
  return (datetime.utcfromtimestamp(timestamp) - datetime(1601, 1, 1)).total_seconds() * 1_000_000

# Convert from Google's time to UNIX timestamp
def from_google_time(time):
  epoch = (time/1_000_000) - (datetime(1970, 1, 1) - datetime(1601, 1, 1)).total_seconds()
  return epoch

def get_links(start_time = None, limit = 5, offset = 0, **options):
  # If there is no start_time provided, defaults to 1 year ago
  if start_time is None:
    start_time = (datetime.now() - timedelta(365)).timestamp()
  elif type(start_time) is datetime:
    start_time = (start_time - datetime(1970, 1, 1)).total_seconds()

  history_file_path = options.get('history_file_path', None)
  ascending = options.get('ascending', True)
  force_copy = options.get('force_copy', False)

  # TODO: Make this OS-Specific
  if history_file_path is None:
    history_file_path = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/History')

  if not os.path.isfile(history_file_path):
    raise IOError("File doesn't exist")

  # Create copy of History file
  tf_name = os.path.relpath('db/chrome.db')

  if force_copy or (not os.path.isfile(tf_name)) or (os.path.getmtime(tf_name) < start_time):
    logging.info("Copying DB file")
    copyfile(history_file_path, tf_name)

  logging.debug("Creating DB Connection")
  conn = sqlite3.connect(tf_name)
  conn.row_factory = sqlite3.Row

  logging.debug('Running Query')

  print ('Select at most {} visits after {}'.format(limit, datetime.utcfromtimestamp(start_time)))

  cur = conn.execute(
    "SELECT COUNT(*) FROM urls WHERE last_visit_time > {}".format(to_google_time(start_time))
  )
  print("{} total entries".format(cur.fetchall()[0][0]))
  print()

  rows = []
  for row in conn.execute("""
  SELECT url, title, last_visit_time
  FROM urls
  WHERE last_visit_time > {time}
  ORDER BY last_visit_time {dir}
  {limit} OFFSET {offset}
  """.format(time=to_google_time(start_time),
             limit=("LIMIT {}".format(limit) if limit > 0 else ""),
             offset=offset,
             dir=("ASC" if ascending else "DESC"))):
    logging.debug(row)
    rows.append({
      "url": row['url'],
      "title":row['title'],
      "time": from_google_time(row['last_visit_time']),
      "datetime": datetime.utcfromtimestamp(from_google_time(row['last_visit_time']))
    })

  logging.debug("Finishing")
  conn.close()

  return rows

def get_bookmarks(start_time = None, limit = 5, offset = 0, **options):
  # If there is no start_time provided, defaults to 1 year ago
  if start_time is None:
    start_time = (datetime.now() - timedelta(365)).timestamp()
  elif type(start_time) is datetime:
    start_time = (start_time - datetime(1970, 1, 1)).total_seconds()

  bookmark_file_path = options.get('bookmark_file_path', None)
  sorted_by_time = options.get('sorted_by_time', True)
  force_copy = options.get('force_copy', False)

  # TODO: Make this OS-Specific
  if bookmark_file_path is None:
    bookmark_file_path = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Bookmarks')

  if not os.path.isfile(bookmark_file_path):
    raise IOError("File doesn't exist")

  data = None
  try:
    data = json.loads(open(bookmark_file_path).read())
  except json.decoder.JSONDecodeError:
    raise IOError("File format incorrect")

  if 'roots' not in data:
    raise IOError("Unable to understand file")

  rows = []
  nodes = []

  for key in ['bookmark_bar', 'other']:
    if key in data['roots']:
      nodes.append(data['roots'][key])

  while True:
    try:
      # This is currently DFS
      # Change to `nodes.pop(0)` for BFS
      elem = nodes.pop()
    except IndexError:
      break

    if elem['type'] == 'folder' and 'children' in elem:
      for child in elem['children']:
        nodes.append(child)
    elif 'url' in elem:
      # Fetch time
      time = int(elem.get('date_added', 0))
      if 'date_modified' in elem:
        time = int(elem.get('date_modified'))

      if time == 0:
        logging.warning("Time not found for a bookmark")
        continue

      time = from_google_time(time)

      if time <= start_time:
        continue

      # If we're returning a fixed number of items in bookmark file order
      if (not sorted_by_time) and limit == 0:
        # If we have already fetched `limit` items
        break

      if (not sorted_by_time) and offset > 0:
        # Bypass `offset` items
        offset -= 1
      else:
        rows.append({
          "url": elem['url'],
          "title": elem.get('name'),
          "time": time,
          "datetime": datetime.utcfromtimestamp(time)
        })

        if (not sorted_by_time):
          # We have selected an item. Reduce `limit`
          limit -= 1
    else:
      logging.warning("Different node type: {}".format(elem))
      pass

  #end while

  if sorted_by_time:
    rows = sorted(rows, key=lambda x: x['time'])[offset : offset+limit]

  logging.debug("Finishing")
  return rows

def get_feedly(start_time = None, limit = 5, offset = 0, **options):
  # If there is no start_time provided, defaults to 1 year ago
  if start_time is None:
    start_time = (datetime.now() - timedelta(365)).timestamp()
  elif type(start_time) is datetime:
    start_time = (start_time - datetime(1970, 1, 1)).total_seconds()

  # TODO
  streamId = "user/fee9ca94-a640-4dd0-93a3-9f6fbfbb85e5/tag/global.saved"
  authHeader = "Az3LMscr9j9aXAzSsN-UNG6FMXrmJp6n9Z399dZFJ3XUoUsWjkmyso8f3ost9O0Yv1rm6VlW5rJeGhZaQr6V1YUWAYBu5XfO-XQD_31F7EfgMVMucqQwOjdPH7iL-PeHYoTYAKJR39f2S5Dgyw5iQSv6bBTwj_mbwSvgkmWPk7OZowKchM9AyfqA3EDDzz9WvSUCrRmGB3Uwj561YddQcPrCYF0dbU6X3pg8esI_9EMdrFot-A6aV7BKvFj1qQ:feedlydev"

  logging.info("Making HTTP Request")

  r = requests.get("http://cloud.feedly.com/v3/streams/contents", {
    "streamId" : streamId,
    "ranked" : "oldest",
    "newerThan" : int(start_time * 1000) + 1, # +1 because we want strictly greater than
    "count" : limit + offset
  }, headers = {
    "Authorization" : authHeader
  })

  rows = []
  if r.status_code == 200:
    for elem in r.json()['items'][-limit:]:
      logging.info(elem)
      time = int(elem.get('actionTimestamp', 0)) / 1000

      url = elem.get('url', None)
      if url is None:
        url = elem.get('canonical', [{}])[0].get('href', None)
      if url is None:
        url = elem.get('canonicalUrl', None)
      if url is None:
        url = elem.get('alternate', [{}])[0].get('href')

      # Not technically correct, but fallback
      origin = False
      if url is None:
        origin = True
        url = elem.get('origin', {}).get('htmlUrl', None)
      if url is None:
        origin = True
        url = elem.get('originId', None)

      if url is None: continue

      if origin:
        logging.warning("Unable to find URL. Using Origin URL")

      rows.append({
        "url": url,
        "title": elem.get('title'),
        "time": time,
        "datetime": datetime.utcfromtimestamp(time)
      })
  else:
    logging.error("Request failed.")
    logging.error(r.text)


  return rows
