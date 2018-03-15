import sqlite3
import os
import sys
import tempfile
import shutil
import datetime

def to_google_time(time):
  return (time - datetime.datetime(1601, 1, 1)).total_seconds() * 1_000_000

file_name = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/History')
if len(sys.argv) >= 2:
  file_name = sys.argv[1]

if not os.path.isfile(file_name):
  print ("File doesn't exist")
  sys.exit(1)

print ("--- Copying DB file")
tf = tempfile.NamedTemporaryFile(delete=False)
shutil.copyfile(file_name, tf.name)

print ("--- Creating DB Connection")
conn = sqlite3.connect(tf.name)

print ('--- Query')
limit = 10
offset = 0
ascending = False
latest_timestamp = datetime.datetime.now() - datetime.timedelta(1)

print ('Select at most {} visits after {}'.format(limit, latest_timestamp))

cur = conn.execute("SELECT COUNT(*) FROM urls WHERE last_visit_time > {}".format(to_google_time(latest_timestamp)))
print("{} total entries".format(cur.fetchall()[0][0]))
print()

for row in conn.execute("""
SELECT url, title, datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), 'unixepoch')
FROM urls
WHERE last_visit_time > {time}
ORDER BY last_visit_time {dir}
LIMIT {limit} OFFSET {offset}
""".format(time=to_google_time(latest_timestamp), limit=limit, offset=offset, dir=("ASC" if ascending else "DESC"))):
  print (row)

print ("Finishing")
conn.close()
tf.close()
os.remove(tf.name)
