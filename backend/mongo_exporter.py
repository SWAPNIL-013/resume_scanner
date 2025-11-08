# mongo_exporter.py
from pymongo import MongoClient
from datetime import datetime
import os

def export_to_mongo(resume_list, mongo_url, db_name="resume_db", collection_name="resumes"):
    """
    Stores resume data in MongoDB collection.
    The 'email' field is treated as a unique key (upsert mode).
    """
    if not mongo_url:
        raise ValueError("MongoDB URL is required")

    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db[collection_name]

     # Enforce email uniqueness at DB level
    collection.create_index("email", unique=True)

    inserted_count = 0
    for resume in resume_list:
        # Ensure timestamp and default fields
        resume["uploaded_at"] = resume.get("uploaded_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Use email as unique key (like primary key)
        if "email" in resume and resume["email"]:
            result = collection.update_one(
                {"email": resume["email"]},
                {"$set": resume},
                upsert=True  # update if exists else insert
            )
            if result.upserted_id or result.modified_count:
                inserted_count += 1
        else:
            collection.insert_one(resume)
            inserted_count += 1

    client.close()
    return {"inserted_count": inserted_count}
