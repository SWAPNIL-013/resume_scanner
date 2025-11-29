# db_fetcher.py

from pymongo import MongoClient
from db_schema import ResumeDBSchema



def clean_mongo_doc(doc: dict) -> dict:
    """
    Convert MongoDB document into clean JSON-safe dict.
    Converts _id to string and removes unwanted Mongo fields.
    """
    doc = dict(doc)  # make a safe copy

    # Convert _id → string so Pydantic can accept it
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])

    return doc


def fetch_resumes(mongo_uri: str, db_name: str, collection: str):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    coll = db[collection]

    documents = list(coll.find({}))
    if not documents:
        raise ValueError("No resumes found in database.")

    validated_resumes = []

    for doc in documents:
        clean_doc = clean_mongo_doc(doc)

        try:
            validated = ResumeDBSchema(**clean_doc)
            validated_resumes.append(validated.model_dump())
        except Exception as e:
            print("❌ Invalid resume skipped:", e)
            continue

    return validated_resumes



# -------------------------------
# 🔥 Test Runner
# -------------------------------
if __name__ == "__main__":

    import json

    mongo_uri = "mongodb+srv://resume_db_user:Swapnil%4013@cluster0.kg6kzel.mongodb.net/?appName=Cluster0"
    db_name = "resume_db_new"
    collection = "resumes_1"

    print("Connecting to MongoDB...\n")

    try:
        resumes = fetch_resumes(mongo_uri, db_name, collection)
        print(json.dumps(resumes, indent=2))
        print(f"\nFetched {len(resumes)} validated resumes\n")

    except Exception as e:
        print("❌ Error:", e)