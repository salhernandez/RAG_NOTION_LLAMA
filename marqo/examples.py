import marqo
import pprint

MQ_INDEX = "my-third-index"

mq = marqo.Client(url='http://localhost:8882')

# Retrieve by document_id
result = mq.index(MQ_INDEX).get_document(document_id="article_591")
pprint.pprint(result)

# Get index stats
results = mq.index(MQ_INDEX).get_stats()
pprint.pprint(results)

# Keyword/Lexical search
result = mq.index(MQ_INDEX).search('marco polo', search_method=marqo.SearchMethods.LEXICAL)
pprint.pprint(result)

#### Images and multimodal
# Multimodal and cross-modal search.
# To power image and text search, Marqo allows users to plug and play with CLIP models from HuggingFace.
# Note that if you do not configure multi modal search, image urls will be treated as strings.
# To start indexing and searching with images, first create an index with a CLIP configuration, as below:

MQ_MULTIMODAL_INDEX = "my-multimodal-index"
settings = {
    "treat_urls_and_pointers_as_images":True,   # allows us to find an image file and index it 
    "model":"ViT-L/14"
}
# response = mq.create_index(MQ_MULTIMODAL_INDEX, **settings)

# Images can then be added within documents as follows.
# You can use urls from the internet (for example S3) or from the disk of the machine:
response = mq.index(MQ_MULTIMODAL_INDEX).add_documents([{
    "My_Image": "https://raw.githubusercontent.com/marqo-ai/marqo-api-tests/mainline/assets/ai_hippo_realistic.png",
    "Description": "The hippopotamus, also called the common hippopotamus or river hippopotamus, is a large semiaquatic mammal native to sub-Saharan Africa",
    "_id": "hippo-facts"
}], tensor_fields=["My_Image"])

# You can then search the image field using text.
results = mq.index(MQ_MULTIMODAL_INDEX).search('animal')
pprint.pprint(results)

# Searching using an image can be achieved by providing the image link.
results = mq.index(MQ_MULTIMODAL_INDEX).search('https://raw.githubusercontent.com/marqo-ai/marqo-api-tests/mainline/assets/ai_hippo_statue.png')
pprint.pprint(results)
####