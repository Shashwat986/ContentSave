## Comprehensive content search

Databases:
1. **Redis:** For storing the frequencies of each word (within the document and overall) in a persistent key-value store. Also stores analytics metrics about most common domain, and a mapping from hash to url.
1. **SQLite:** For storing URL data and metadata
1. **ElasticSearch:** For keyword search

Steps
1. Fetch data and metadata of url
1. Store data and metadata in SQLite
1. Store word frequencies in Redis
1. After fetching N urls, run a job to update ElasticSearch with word frequencies. This will be long-running, because will require recalculation of all frequencies.
