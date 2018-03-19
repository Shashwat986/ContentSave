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

  # TODO: Fetch and add metadata also
  return " ".join(soup.get_text().strip().split())

def get_html(url):
  r = requests.get(url)
  if r.status_code != 200:
    raise Exception("Error with reading url")

  return parse_html(r.text)

def get_headless_html(url, wait=2):
  try:
    driver = webdriver.Chrome(chrome_options=options)
  except (FileNotFoundError, WebDriverException):
    # ChromeDriver is not available
    print ("""
    For best results, please install ChromeDriver

      $ brew install chromedriver

    Reverting to Requests, which will not load dynamic content.
    """)
    return get_html(url)

  driver.get(url)
  driver.implicitly_wait(wait)
  src = driver.page_source
  driver.quit()

  return parse_html(src)

