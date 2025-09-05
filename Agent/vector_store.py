import time
from tqdm import tqdm
from langchain_community.vectorstores import Milvus
from langchain_openai import AzureOpenAIEmbeddings
from pymilvus import utility, connections
import config

def connect_to_milvus():
    """Establishes a connection to the Milvus server if not already connected."""
    if not connections.has_connection("default"):
        print("Establishing new connection to Milvus ")
        connections.connect("default", host=config.MILVUS_HOST, port=config.MILVUS_PORT)
    else:
        print("Using existing connection to Milvus ")

def get_milvus_retrievers():
    """Initializes connection to Milvus and returns LangChain retrievers."""
    connect_to_milvus() # Ensure connection is active
    
    print(" Initializing Milvus Vector Store Retrievers ")
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=config.AZURE_EMBEDDING_DEPLOYMENT_NAME,
        api_key=config.AZURE_API_KEY,
        azure_endpoint=config.AZURE_API_BASE,
        api_version=config.AZURE_API_VERSION
    )

    if not utility.has_collection(config.QURAN_COLLECTION) or not utility.has_collection(config.HADITH_COLLECTION):
        print("One or more collections not found in Milvus. Please run the '/ingest' endpoint first.")
        return None, None
    
    quran_vector_store = Milvus(embeddings, collection_name=config.QURAN_COLLECTION, connection_args={"host": config.MILVUS_HOST, "port": config.MILVUS_PORT})
    hadith_vector_store = Milvus(embeddings, collection_name=config.HADITH_COLLECTION, connection_args={"host": config.MILVUS_HOST, "port": config.MILVUS_PORT})
    
    print(" Milvus Retrievers Initialized Successfully ")
    return quran_vector_store.as_retriever(search_kwargs={"k": 5}), hadith_vector_store.as_retriever(search_kwargs={"k": 5})

def ingest_data_to_milvus(collection_name, documents):
    """Ingests chunked documents into a Milvus collection in batches."""
    connect_to_milvus() # Ensure connection is active

    print(f" Starting data ingestion for '{collection_name}' ")
    if utility.has_collection(collection_name):
        print(f"Collection '{collection_name}' already exists. Dropping for fresh ingestion.")
        utility.drop_collection(collection_name)

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=config.AZURE_EMBEDDING_DEPLOYMENT_NAME,
        api_key=config.AZURE_API_KEY,
        azure_endpoint=config.AZURE_API_BASE,
        api_version=config.AZURE_API_VERSION
    )
    
    batch_size = 500
    vector_store = None

    print(f"Ingesting {len(documents)} documents in batches of {batch_size}...")
    for i in tqdm(range(0, len(documents), batch_size)):
        batch = documents[i:i + batch_size]
        
        if vector_store is None:
            vector_store = Milvus.from_documents(
                batch, embeddings, collection_name=collection_name,
                connection_args={"host": config.MILVUS_HOST, "port": config.MILVUS_PORT}
            )
        else:
            vector_store.add_documents(batch)
        
        print(f"  - Batch {i//batch_size + 1} ingested. Pausing for 5 seconds...")
        time.sleep(5)

    print(f" Data ingestion for '{collection_name}' complete ")