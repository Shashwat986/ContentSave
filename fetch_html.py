import logging
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup as BS
import re
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

class Status:
  NO_CONNECTION = 0
  URL_INCORRECT = 1
  ALL_OK        = 2

  def __init__(self, status):
    self.status = status

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument("--mute-audio")

def parse_html(text):
  soup = BS(text, "html5lib")

  for tag in soup(['script', 'style']):
    tag.decompose()

  for tag in soup.find_all(True, string=lambda x: True):
    # Adding spaces around all text strings
    if tag.string is not None:
      tag.string = ' ' + tag.string + ' '

  body = " ".join(soup.get_text().strip().split())
  body = re.sub('[^A-Za-z0-9 ]+', ' ', body).lower()

  description = None
  if soup.find('meta', property="og:description"):
    description = soup.find('meta', property="og:description")['content']
    body += " " + re.sub('[^A-Za-z0-9 ]+', ' ', description).lower()

  keywords = None
  if soup.find('meta', attrs={"name":"keywords"}):
    keywords = soup.find('meta', attrs={"name":"keywords"})['content']
    body += " " + re.sub('[^A-Za-z0-9 ]+', ' ', keywords).lower()

  title = None
  if soup.find('title') and soup.find('title').string:
    title = soup.find('title').string
    body += " " + re.sub('[^A-Za-z0-9 ]+', ' ', title).lower()
  if soup.find('meta', property="og:title"):
    title = soup.find('meta', property="og:title")['content']
    body += " " + re.sub('[^A-Za-z0-9 ]+', ' ', title).lower()

  return {
    'body': body,
    'description': description,
    'keywords': keywords,
    'title': title
  }

def check_url(url):
  status = Status(Status.NO_CONNECTION)
  try:
    socket.create_connection(("www.google.com", 80))
    status = Status(Status.URL_INCORRECT)

    socket.create_connection((urlparse(url).netloc, 80))
    assert requests.head(url).status_code < 400
    status = Status(Status.ALL_OK)

    return status
  except (AssertionError, OSError) as e:
    logging.info("Unable to find URL {}. Error:".format(url))
    logging.info(e)
    return status
  except Exception as e:
    logging.exception("Unknown Error")
    return status

  return status

def get_html(url):
  status = check_url(url)
  if status.status != Status.ALL_OK:
    return status

  r = requests.get(url)
  if r.status_code != 200:
    logging.warning("Status Code was not 200 for {}.".format(url))

  return parse_html(r.text)

def get_headless_html(url, wait=10):
  try:
    driver = webdriver.Chrome(chrome_options=options)
  except (FileNotFoundError, WebDriverException):
    # ChromeDriver is not available
    logging.warning ("""
    For best results, please install ChromeDriver

      $ brew install chromedriver

    Reverting to Requests, which will not load dynamic content.
    """)
    return get_html(url)

  status = check_url(url)
  if status.status != Status.ALL_OK:
    return status

  logging.debug("Starting Selenium processing of {}".format(url))

  driver.get(url)
  driver.execute_script("setTimeout(function(){window.stop()}, %d)" % (wait * 1000))

  src = driver.page_source
  driver.quit()
  logging.debug("Finished Selenium processing of {}".format(url))

  return parse_html(src)

