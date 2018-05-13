import logging
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup as BS
import re
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException

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
  if soup.find('meta', property="og:description") and soup.find('meta', property="og:description").get('content', None):
    description = soup.find('meta', property="og:description")['content']
    body += " " + re.sub('[^A-Za-z0-9 ]+', ' ', description).lower()

  keywords = None
  if soup.find('meta', attrs={"name":"keywords"}) and soup.find('meta', attrs={"name":"keywords"}).get('content', None):
    keywords = soup.find('meta', attrs={"name":"keywords"})['content']
    body += " " + re.sub('[^A-Za-z0-9 ]+', ' ', keywords).lower()

  title = None
  if soup.find('title') and soup.find('title').string:
    title = soup.find('title').string
    body += " " + re.sub('[^A-Za-z0-9 ]+', ' ', title).lower()
  if soup.find('meta', property="og:title") and soup.find('meta', property="og:title").get('content', None):
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

    socket.create_connection((urlparse(url).netloc, 80), timeout = 20)
    assert requests.head(url, timeout=2).status_code < 400
    status = Status(Status.ALL_OK)

    return status
  except (AssertionError, OSError) as e:
    logging.info("Unable to find URL {}. Error:".format(url))
    logging.info(e)
    return status
  except requests.exceptions.Timeout as e:
    logging.info("Unable to make HEAD request")
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

  try:
    r = requests.get(url)
  except Exception as e:
    logging.exception("Unknown Error")
    return Status(Status.URL_INCORRECT)

  if r.status_code != 200:
    logging.warning("Status Code was not 200 for {}.".format(url))

  return parse_html(r.text)

def get_headless_html(url, wait = 30):
  try:
    driver = webdriver.Chrome(chrome_options=options)
    driver.set_page_load_timeout(wait)
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

  try:
    driver.get(url)
    driver.execute_script("window.x = 1; setTimeout(function(){window.stop(); window.x = 2;}, %d)" % (wait * 1000))

    src = driver.page_source
    print(driver.execute_script("return window.x"))
  except TimeoutException:
    logging.exception("Falling back to Requests because selenium timed out")
    return get_html(url)
  except Exception as e:
    logging.exception("Unknown Error")
    return Status(Status.URL_INCORRECT)
  finally:
    driver.quit()

  logging.debug("Finished Selenium processing of {}".format(url))

  return parse_html(src)

