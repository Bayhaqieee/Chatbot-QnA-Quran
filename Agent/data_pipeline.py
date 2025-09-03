import os
os.environ['KAGGLE_CONFIG_DIR'] = '.'

import kaggle
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def download_and_extract_datasets():
    """Downloads and extracts datasets from Kaggle if they don't exist."""
    datasets_dir = 'datasets'
    os.makedirs(datasets_dir, exist_ok=True)
    
    hadith_path = os.path.join(datasets_dir, 'all_hadiths_clean.csv')
    if not os.path.exists(hadith_path):
        print("Downloading Hadith dataset...")
        # The API will now correctly find kaggle.json in your project root
        kaggle.api.dataset_download_files('fahd09/hadith-dataset', path=datasets_dir, unzip=True)
        print("Hadith dataset downloaded.")

    quran_path = os.path.join(datasets_dir, 'main_df.csv')
    if not os.path.exists(quran_path):
        print("Downloading Quran dataset...")
        kaggle.api.dataset_download_files('alizahidraja/quran-nlp', path=datasets_dir, unzip=True)
        # The file is inside a 'data' subdirectory after unzipping
        if os.path.exists(os.path.join(datasets_dir, 'data', 'main_df.csv')):
            os.rename(os.path.join(datasets_dir, 'data', 'main_df.csv'), quran_path)
        print("Quran dataset downloaded.")

def load_and_chunk_data():
    """Loads data from local CSVs and splits them into chunks."""
    print("--- Loading and Processing Data ---")
    
    # The setup_kaggle_api function is no longer needed with the environment variable fix.
    download_and_extract_datasets()

    try:
        quran_loader = CSVLoader(file_path='datasets/main_df.csv', encoding='utf-8')
        quran_docs = quran_loader.load()

        hadith_loader = CSVLoader(file_path='datasets/all_hadiths_clean.csv', encoding='utf-8')
        hadith_docs = hadith_loader.load()
        
    except FileNotFoundError as e:
        print(f"Error: {e}. One of the dataset CSV files is missing.")
        return None, None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    quran_chunks = text_splitter.split_documents(quran_docs)
    hadith_chunks = text_splitter.split_documents(hadith_docs)

    print(f"Data chunked: {len(quran_chunks)} Quran docs, {len(hadith_chunks)} Hadith docs.")
    return quran_chunks, hadith_chunks