import os
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import kaggle
import pandas as pd

def setup_kaggle_api():
    os.makedirs(os.path.expanduser('~/.kaggle'), exist_ok=True)
    if os.path.exists('kaggle.json'):
        destination = os.path.expanduser('~/.kaggle/kaggle.json')
        os.rename('kaggle.json', destination)
        os.chmod(destination, 0o600)
    elif not os.path.exists(os.path.expanduser('~/.kaggle/kaggle.json')):
        raise FileNotFoundError("kaggle.json not found. Please place it in your project root.")

def download_and_extract_datasets():
    datasets_dir = 'datasets'
    os.makedirs(datasets_dir, exist_ok=True)
    hadith_path = os.path.join(datasets_dir, 'all_hadiths_clean.csv')
    quran_path = os.path.join(datasets_dir, 'main_df.csv')

    if not os.path.exists(hadith_path):
        print("Downloading Hadith dataset...")
        kaggle.api.dataset_download_files('fahd09/hadith-dataset', path=datasets_dir, unzip=True)
    if not os.path.exists(quran_path):
        print("Downloading Quran dataset...")
        kaggle.api.dataset_download_files('alizahidraja/quran-nlp', path=datasets_dir, unzip=True)
        if os.path.exists(os.path.join(datasets_dir, 'data', 'main_df.csv')):
            os.rename(os.path.join(datasets_dir, 'data', 'main_df.csv'), quran_path)

def load_and_chunk_data():
    print("--- Loading and Processing Data for AI ---")
    setup_kaggle_api()
    download_and_extract_datasets()
    quran_loader = CSVLoader(file_path='datasets/main_df.csv', encoding='utf-8')
    hadith_loader = CSVLoader(file_path='datasets/all_hadiths_clean.csv', encoding='utf-8')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    quran_chunks = text_splitter.split_documents(quran_loader.load())
    hadith_chunks = text_splitter.split_documents(hadith_loader.load())
    return quran_chunks, hadith_chunks

def load_quran_for_dictionary():
    """Loads and prepares the Quran dataset for the dictionary view."""
    try:
        df = pd.read_csv('datasets/main_df.csv')
        # Select and rename columns for clarity
        quran_data = df[['EnglishTitle', 'Surah', 'Ayat', 'Translation - Arthur J']].rename(columns={
            'EnglishTitle': 'surah_name',
            'Surah': 'surah_number',
            'Ayat': 'ayat_number',
            'Translation - Arthur J': 'translation'
        })
        return quran_data.to_dict(orient='records')
    except FileNotFoundError:
        return []

def load_hadith_for_dictionary():
    """Loads and prepares the Hadith dataset for the dictionary view."""
    try:
        df = pd.read_csv('datasets/all_hadiths_clean.csv')
        # Select and fill missing values
        hadith_data = df[['source', 'chapter', 'text_en']].fillna('N/A')
        return hadith_data.to_dict(orient='records')
    except FileNotFoundError:
        return []