import logging
from model import redis_client, Url, ESUrl
from peewee import fn
from elasticsearch_dsl import Search

def find_docs(search_terms, offset = 0, limit = 10):
  if type(search_terms) == list:
    search_terms = " ".join(search_terms)

  if type(search_terms) != str:
    logging.error("Invalid argument type. Expected str or list")
    return []

  rowids = []
  for hit in Search().query('multi_match', **{
    "query" : search_terms,
    "type" : "most_fields",
    "fields" : ["body", "tfidf^2"],
    "fuzziness": "AUTO"
  }).source(False).highlight('body').execute()[ offset : (offset+limit) ]:
    rowid = hit.meta.id

    doc_terms = set([word[4:-5] for word in hit.meta.highlight.body])

    rowids.append({
      "rowid" : rowid,
      "terms" : doc_terms,
      "highlights" : hit.meta.highlight.body,
      "score" : hit.meta.score
    })

  return sorted(rowids, key=lambda x: -x['score'])

def get_tfidf_of_word(word, rowid):
  term_score = float(redis_client.zscore("doc:{}".format(rowid), word))
  doc_score = float(redis_client.zscore("doc:all", word))

  return 1.0 * term_score / doc_score

def get_metadata():
  print ("Total URLs processed:", Url.select().count())
  print ("Vocabulary Size:", redis_client.zcard('doc:all'))

  freq_domains = list(
    map(
      lambda x: x.domain,
      Url.select(
        Url.domain,
        fn.SUM(Url.visit_count).alias('sc')
      ).group_by(Url.domain)
      .order_by(-fn.SUM(Url.visit_count))
      [0:4]
    )
  )

  print ("Most frequent domains:", ", ".join(freq_domains))
