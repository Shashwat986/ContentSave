import sqlite3
import os
import sys
from tempfile import NamedTemporaryFile
from shutil import copyfile
from datetime import datetime, timedelta

def to_google_time(timestamp):
  return (datetime.utcfromtimestamp(timestamp) - datetime(1601, 1, 1)).total_seconds() * 1_000_000

def from_google_time(time):
  epoch = (time/1_000_000) - (datetime(1970, 1, 1) - datetime(1601, 1, 1)).total_seconds()
  return epoch

def get_links(start_time = None, limit = 5, offset = 0, history_file_path = None, ascending = True):
  if history_file_path is None:
    # TODO: Make this OS-Specific
    history_file_path = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/History')

  if not os.path.isfile(history_file_path):
    raise IOError("File doesn't exist")
    sys.exit(1)

  print ("--- Copying DB file")
  tf = NamedTemporaryFile(delete=False)
  copyfile(history_file_path, tf.name)

  print ("--- Creating DB Connection")
  conn = sqlite3.connect(tf.name)

  print ('--- Query')
  if start_time is None:
    start_time = (datetime.now() - timedelta(1)).timestamp()
  elif type(start_time) is datetime:
    start_time = (start_time - datetime(1970, 1, 1)).total_seconds()

  print ('Select at most {} visits after {}'.format(limit, datetime.utcfromtimestamp(start_time)))

  cur = conn.execute("SELECT COUNT(*) FROM urls WHERE last_visit_time > {}".format(to_google_time(start_time)))
  print("{} total entries".format(cur.fetchall()[0][0]))
  print()

  rows = []
  for row in conn.execute("""
  SELECT url, title, last_visit_time
  FROM urls
  WHERE last_visit_time > {time}
  ORDER BY last_visit_time {dir}
  LIMIT {limit} OFFSET {offset}
  """.format(time=to_google_time(start_time), limit=limit, offset=offset, dir=("ASC" if ascending else "DESC"))):
    print (row)
    rows.append({
      "url": row[0],
      "title":row[1],
      "time": from_google_time(row[2])
    })

  print ("--- Finishing")
  conn.close()
  tf.close()
  os.remove(tf.name)

  return rows
