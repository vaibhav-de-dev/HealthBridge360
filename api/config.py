import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "healthbridge360")
DB_USER = os.getenv("DB_USER", "healthbridge_api")
DB_PASSWORD = os.getenv("DB_PASSWORD", "healthbridge_api_dev")
