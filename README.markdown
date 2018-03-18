## Comprehensive content search

Databases:
1. **Redis:** For storing the frequencies of each word (within the document and overall) in a persistent key-value store. Also stores analytics metrics about most common domain, and a mapping from hash to url.
1. **SQLite:** For long-term storage of word frequencies, and for calculating TF-IDF values in an easier manner?
1. **ElasticSearch:** For keyword search
