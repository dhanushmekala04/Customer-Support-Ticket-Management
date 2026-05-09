"""
Run this once to inspect and fix FAQ records in MongoDB.

    python -m src.utils.faq_debug
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pymongo import MongoClient
from src.config import config


def main():
    client = MongoClient(config.MONGO_URI)
    db = client[config.MONGO_DB_NAME]
    collection = db[config.FAQ_COLLECTION]

    total = collection.count_documents({})
    print(f"\n{'='*60}")
    print(f"Collection : {config.MONGO_DB_NAME}.{config.FAQ_COLLECTION}")
    print(f"Total docs : {total}")
    print(f"{'='*60}\n")

    if total == 0:
        print("⚠️  Collection is empty — no FAQs found.")
        print("   Run: python -m src.agents.faq_agent add\n")
        return

    # Print all records
    for doc in collection.find().sort("id", 1):
        print(f"[{doc.get('id', '?')}] {doc.get('category', '?')}")
        print(f"  Q : {doc.get('question', '—')}")
        print(f"  A : {doc.get('answer', '—')[:120]}")
        print()

    # Check for missing required fields
    bad = list(collection.find({
        "$or": [
            {"id": {"$exists": False}},
            {"category": {"$exists": False}},
            {"question": {"$exists": False}},
            {"answer": {"$exists": False}},
        ]
    }))

    if bad:
        print(f"⚠️  {len(bad)} record(s) missing required fields:")
        for b in bad:
            print(f"   _id={b['_id']} → keys present: {list(b.keys())}")
        fix = input("\nRemove these broken records? (y/n): ").strip().lower()
        if fix == 'y':
            ids = [b['_id'] for b in bad]
            collection.delete_many({"_id": {"$in": ids}})
            print(f"✅ Removed {len(ids)} broken record(s)")
    else:
        print("✅ All records look healthy.")

    # Re-sequence IDs if gaps exist
    all_docs = list(collection.find().sort("id", 1))
    needs_reseq = any(doc.get('id') != i+1 for i, doc in enumerate(all_docs))
    if needs_reseq:
        print("\n⚠️  ID sequence has gaps. Re-sequencing...")
        for i, doc in enumerate(all_docs):
            collection.update_one({"_id": doc["_id"]}, {"$set": {"id": i+1}})
        print("✅ IDs re-sequenced.")


if __name__ == "__main__":
    main()