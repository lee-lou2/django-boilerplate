import os

import firebase_admin
from django.conf import settings
from firebase_admin import credentials


def initialize_firebase():
    """Firebase Admin SDK 초기화"""
    # 이미 초기화 되었는지 확인
    if not firebase_admin._apps:
        try:
            service_account_key_path = os.path.join(
                settings.BASE_DIR, "secrets/serviceAccountKey.json"
            )
            cred = credentials.Certificate(service_account_key_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")
