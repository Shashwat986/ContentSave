from model import sqlite_db, Url, UrlIndex
sqlite_db.connect()
sqlite_db.create_tables([Url, UrlIndex])
