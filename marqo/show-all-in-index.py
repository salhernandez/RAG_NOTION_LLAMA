import marqo
import pprint

MQ_INDEX = "my-third-index"

mq = marqo.Client(url='http://localhost:8882')

#                                         Start, limit
result = mq.index(MQ_INDEX).get_documents(0, 1000)

pprint.pprint(result)