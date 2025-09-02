import os
import zipfile
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import kaggle

def setup_kaggle_api():
    """Sets up the Kaggle API credentials."""
    # The kaggle library automatically looks for ~/.kaggle/kaggle.json
    # We can programmatically set it up if needed, but placing the file is easier.
    # This function ensures the directory exists and has the right permissions.
    os.makedirs(os.path.expanduser('~/.kaggle'), exist_ok=True)
    if os.path.exists('kaggle.json'):
        os.rename('kaggle.json', os.path.expanduser('~/.kaggle/kaggle.json'))
        os.chmod(os.path.expanduser('~/.kaggle/kaggle.json'), 0o600)
    elif not os.path.exists(os.path.expanduser('~/.kaggle/kaggle.json')):
        raise FileNotFoundError("kaggle.json not found in project root or ~/.kaggle/")

def download_and_extract_datasets():
    """Downloads and extracts datasets from Kaggle if they don't exist."""
    datasets_dir = 'datasets'
    os.makedirs(datasets_dir, exist_ok=True)
    
    # Dataset 1: Hadith
    hadith_path = os.path.join(datasets_dir, 'all_hadiths_clean.csv')
    if not os.path.exists(hadith_path):
        print("Downloading Hadith dataset...")
        kaggle.api.dataset_download_files('fahd09/hadith-dataset', path=datasets_dir, unzip=True)
        print("Hadith dataset downloaded.")

    # Dataset 2: Quran
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
    
    setup_kaggle_api()
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

    print(f"Quran data chunked into {len(quran_chunks)} documents.")
    print(f"Hadith data chunked into {len(hadith_chunks)} documents.")
    print("--- Data Loading and Processing Complete ---")
    
    return quran_chunks, hadith_chunks