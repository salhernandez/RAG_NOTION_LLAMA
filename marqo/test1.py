import marqo
import pprint

mq = marqo.Client(url='http://localhost:8882')

# * Needed to Create an index
mq.create_index("my-third-index", model="hf/e5-base-v2")

mq.index("my-third-index").add_documents([
    {
        "Title": "The Travels of Marco Polo",
        "Description": "A 13th-century travelogue describing Polo's travels"
    }, 
    {
        "Title": "Frodo Baggins",
        "Description": "Story of the adventures of a hobbit"
    }, 
    {
        "Title": "Extravehicular Mobility Unit (EMU)",
        "Description": "The EMU is a spacesuit that provides environmental protection, "
                       "mobility, life support, and communications for astronauts",
        "_id": "article_591"
    }],
    tensor_fields=["Description"]
)
# * END

# Use index desired!
results = mq.index("my-third-index").search(
    q="Who is Frodo?"
)

pprint.pprint(results)