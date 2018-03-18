from bs4 import BeautifulSoup as BS
import requests
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('headless')

def parse_html(text):
  soup = BS(text, "html5lib")

  for tag in soup(['script', 'style']):
    tag.decompose()

  for tag in soup.find_all(True, string=lambda x: True):
    # Adding spaces around all text strings
    if tag.string is not None:
      tag.string = ' ' + tag.string + ' '

  return " ".join(soup.get_text().strip().split())

def get_html(url):
  r = requests.get(url)
  if r.status_code != 200:
    raise Exception("Error with reading url")

  return parse_html(r.text)

def get_headless_html(url, wait=2):
  driver = webdriver.Chrome(chrome_options=options)
  driver.get(url)
  driver.implicitly_wait(wait)
  src = driver.page_source
  driver.quit()

  return parse_html(src)

