import os
import chromadb
import voyageai
from dotenv import load_dotenv

load_dotenv()

client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
db = chromadb.PersistentClient(path="./cases_db")
collection = db.get_or_create_collection("my_cases")

cases_folder = "./cases_text"

for filename in os.listdir(cases_folder):
    if not filename.endswith(".txt"):
        continue

    filepath = os.path.join(cases_folder, filename)
    with open(filepath, "r", errors="ignore") as f:
        text = f.read().strip()

    if not text:
        print(f"Skipping empty file: {filename}")
        continue

    # voyage-law-2 with input_type="document" optimizes embeddings for storage/retrieval
    result = client.embed([text], model="voyage-law-2", input_type="document")
    vector = result.embeddings[0]

    case_id = filename.replace(".txt", "")
    collection.upsert(
        ids=[case_id],
        embeddings=[vector],
        documents=[text],
        metadatas=[{"filename": filename, "case": case_id}]
    )
    print(f"Indexed: {filename}")

print(f"Done. {collection.count()} cases in index.")
