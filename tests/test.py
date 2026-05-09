 """
MongoDB Connection Test
"""

from pymongo import MongoClient




try:

    # =============================================
    # Connect MongoDB
    # =============================================

    client = MongoClient(
        
    )

    # =============================================
    # Test Connection
    # =============================================

    client.admin.command("ping")

    print(
        "✅ MongoDB connected successfully"
    )

    # =============================================
    # Select Database
    # =============================================

    db = client[
        config.MONGO_DB_NAME
    ]

    print(
        f"✅ Database Connected: "
        f"{config.MONGO_DB_NAME}"
    )

    # =============================================
    # Select FAQ Collection
    # =============================================

    faq_collection = db[
        config.FAQ_COLLECTION
    ]

    print(
        f"✅ Collection Connected: "
        f"{config.FAQ_COLLECTION}"
    )

    # =============================================
    # Insert Test Record
    # =============================================

    test_document = {

        "category":
            "TEST",

        "question":
            "MongoDB Test Question",

        "answer":
            "MongoDB Test Answer"
    }

    result = faq_collection.insert_one(
        test_document
    )

    print(
        f"✅ Test record inserted: "
        f"{result.inserted_id}"
    )

    # =============================================
    # Fetch Records
    # =============================================

    records = list(
        faq_collection.find(
            {},
            {"_id": 0}
        )
    )

    print("\n📌 Current Records:\n")

    for record in records:

        print(record)

except Exception as e:

    print(
        f"❌ MongoDB Error: {e}"
    )
