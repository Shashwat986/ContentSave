import logging
from bs4 import BeautifulSoup as BS
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

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

  description = None
  if soup.find('meta', property="og:description"):
    description = soup.find('meta', property="og:description")['content']

  keywords = None
  if soup.find('meta', attrs={"name":"keywords"}):
    keywords = soup.find('meta', attrs={"name":"keywords"})['content']

  title = None
  if soup.find('title'):
    title = soup.find('title').string
  if soup.find('meta', property="og:title"):
    title = soup.find('meta', property="og:title")['content']

  return {
    'body': body,
    'meta:description': description,
    'meta:keywords': keywords,
    'title': title
  }

def get_html(url):
  r = requests.get(url)
  if r.status_code != 200:
    logging.warning("Status Code was not 200 for {}.".format(url))

  return parse_html(r.text)

def get_headless_html(url, wait=2):
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

  logging.debug("Starting Selenium processing of {}".format(url))
  driver.get(url)
  driver.implicitly_wait(wait)
  src = driver.page_source
  driver.quit()
  logging.debug("Finished Selenium processing of {}".format(url))

  return parse_html(src)

