import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure Credentials
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_API_BASE = os.getenv("AZURE_API_BASE")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME")
AZURE_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_CHAT_DEPLOYMENT_NAME")

# Serper Credentials
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Milvus Configuration
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
QURAN_COLLECTION = os.getenv("MILVUS_QURAN_COLLECTION")
HADITH_COLLECTION = os.getenv("MILVUS_HADITH_COLLECTION")