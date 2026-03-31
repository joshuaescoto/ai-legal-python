import os
import sys
import chromadb
import voyageai
from dotenv import load_dotenv

load_dotenv()

question = " ".join(sys.argv[1:])
if not question:
    print("Usage: python cases_query.py 'your question here'")
    sys.exit(1)

client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
db = chromadb.PersistentClient(path="./cases_db")
collection = db.get_collection("my_cases")

# Asymmetric query embedding
result = client.embed([question], model="voyage-law-2", input_type="query")
query_vector = result.embeddings[0]

# n_results controls how many cases are returned — tune based on context window
results = collection.query(
    query_embeddings=[query_vector],
    n_results=4
)

for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
    print(f"\n--- CASE {i+1}: {meta['case']} ---\n")
    print(doc[:3000])  # truncate to manage LLM context length
