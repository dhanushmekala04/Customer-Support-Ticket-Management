"""
Seed the MongoDB FAQ collection with initial data.

    python -m src.utils.seed_faqs
"""

import sys
import os
import certifi
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pymongo import MongoClient
from src.config import config

FAQS = [
    # ── TECHNICAL ──────────────────────────────────────────────
    {
        "category": "TECHNICAL",
        "question": "How do I reset my password?",
        "answer": (
            "To reset your password, click 'Forgot Password' on the login page, "
            "enter your registered email address, and follow the link sent to your inbox. "
            "The link expires after 30 minutes."
        ),
    },
    {
        "category": "TECHNICAL",
        "question": "Why is my application running slowly?",
        "answer": (
            "Slow performance is often caused by high memory usage, too many background processes, "
            "or a poor network connection. Try clearing your cache, restarting the app, "
            "and ensuring your device meets the minimum system requirements."
        ),
    },
    {
        "category": "TECHNICAL",
        "question": "How do I install the latest update?",
        "answer": (
            "Go to Settings → About → Check for Updates. If an update is available, "
            "click 'Download and Install'. Make sure you have a stable internet connection "
            "and at least 500 MB of free disk space before updating."
        ),
    },
    {
        "category": "TECHNICAL",
        "question": "The app crashes when uploading large files. What should I do?",
        "answer": (
            "File uploads are limited to 100 MB per file. For larger files, "
            "compress them first or split into smaller parts. Also ensure your browser "
            "or app is up to date. If the issue persists, clear your browser cache and retry."
        ),
    },
    {
        "category": "TECHNICAL",
        "question": "How do I enable two-factor authentication?",
        "answer": (
            "Go to Account Settings → Security → Two-Factor Authentication and click Enable. "
            "You can use an authenticator app (Google Authenticator, Authy) or receive "
            "codes via SMS. It is strongly recommended to enable 2FA for account security."
        ),
    },
    {
        "category": "TECHNICAL",
        "question": "I cannot log in to my account. What should I do?",
        "answer": (
            "First, ensure your email and password are correct (check Caps Lock). "
            "Try resetting your password if needed. If your account is locked after "
            "multiple failed attempts, wait 15 minutes or contact support to unlock it."
        ),
    },
    {
        "category": "TECHNICAL",
        "question": "How do I integrate the API with my application?",
        "answer": (
            "Full API documentation is available at /docs/api. You will need an API key "
            "from your dashboard under Settings → API Keys. We support REST with JSON. "
            "Rate limits are 1000 requests per minute on the standard plan."
        ),
    },

    # ── BILLING ────────────────────────────────────────────────
    {
        "category": "BILLING",
        "question": "How do I cancel my subscription?",
        "answer": (
            "You can cancel your subscription at any time from Account Settings → Billing → "
            "Cancel Subscription. Your access continues until the end of the current billing period. "
            "No refunds are issued for partial months."
        ),
    },
    {
        "category": "BILLING",
        "question": "Why was I charged twice this month?",
        "answer": (
            "Double charges can occur if a payment failed and was retried, or if two separate "
            "subscriptions are active. Please check your billing history under Account → Billing. "
            "If an error is confirmed, contact support with your transaction IDs for a refund."
        ),
    },
    {
        "category": "BILLING",
        "question": "How do I update my payment method?",
        "answer": (
            "Go to Account Settings → Billing → Payment Methods and click 'Add New Card'. "
            "Once added, set it as the default method. Old cards can be removed after "
            "a successful charge on the new card."
        ),
    },
    {
        "category": "BILLING",
        "question": "Can I get a refund?",
        "answer": (
            "Refunds are available within 7 days of purchase for annual plans. "
            "Monthly plans are non-refundable once the billing cycle starts. "
            "To request a refund, contact support with your order number and reason."
        ),
    },
    {
        "category": "BILLING",
        "question": "How do I download my invoice?",
        "answer": (
            "Invoices are available under Account Settings → Billing → Invoice History. "
            "Click the download icon next to any invoice to save it as a PDF. "
            "Invoices are generated automatically on each billing date."
        ),
    },
    {
        "category": "BILLING",
        "question": "What payment methods do you accept?",
        "answer": (
            "We accept Visa, Mastercard, American Express, and PayPal. "
            "For enterprise plans, bank transfers and purchase orders are also available. "
            "All payments are processed securely via Stripe."
        ),
    },

    # ── GENERAL ────────────────────────────────────────────────
    {
        "category": "GENERAL",
        "question": "How do I contact customer support?",
        "answer": (
            "You can reach our support team 24/7 via live chat on the website, "
            "by emailing support@example.com, or by calling +1-800-000-0000 "
            "Monday to Friday, 9 AM – 6 PM EST."
        ),
    },
    {
        "category": "GENERAL",
        "question": "What are your business hours?",
        "answer": (
            "Our support team is available Monday to Friday, 9 AM – 6 PM EST. "
            "Live chat and the help centre are available 24/7. "
            "Response times for email are typically within 4 business hours."
        ),
    },
    {
        "category": "GENERAL",
        "question": "How do I change my account email address?",
        "answer": (
            "Go to Account Settings → Profile → Email Address and enter your new email. "
            "A verification link will be sent to the new address. "
            "Your email will only update after you click the verification link."
        ),
    },
    {
        "category": "GENERAL",
        "question": "How do I delete my account?",
        "answer": (
            "Account deletion is permanent and cannot be undone. To delete your account, "
            "go to Account Settings → Privacy → Delete Account and confirm with your password. "
            "All data will be permanently removed within 30 days."
        ),
    },
    {
        "category": "GENERAL",
        "question": "Where can I find the user documentation?",
        "answer": (
            "Full documentation is available at docs.example.com. "
            "It includes getting started guides, API references, tutorials, and FAQs. "
            "You can also access it from the Help menu inside the application."
        ),
    },
]


def seed():
    client = MongoClient(config.MONGO_URI, tlsCAFile=certifi.where())
    db = client[config.MONGO_DB_NAME]
    collection = db[config.FAQ_COLLECTION]
 
    existing = collection.count_documents({})
    if existing > 0:
        confirm = input(
            f"⚠️  Collection already has {existing} record(s). "
            f"Clear and re-seed? (y/n): "
        ).strip().lower()
        if confirm != 'y':
            print("❌ Aborted.")
            return
        collection.delete_many({})
        print(f"🗑️  Cleared {existing} existing record(s).")
 
    docs = [{"id": i + 1, **faq} for i, faq in enumerate(FAQS)]
    collection.insert_many(docs)
 
    print(f"\n✅ Seeded {len(docs)} FAQs into "
          f"{config.MONGO_DB_NAME}.{config.FAQ_COLLECTION}\n")
 
    for doc in docs:
        print(f"  [{doc['id']}] {doc['category']} — {doc['question']}")
 
    print()
 
 
if __name__ == "__main__":
    seed()