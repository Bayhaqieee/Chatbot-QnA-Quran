import os
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import kaggle
import pandas as pd
import re

def slugify(s):
    """Simple function to create a URL-friendly slug from a string."""
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s

def check_kaggle_api():
    kaggle_dir = os.path.expanduser('~/.kaggle')
    api_key_path = os.path.join(kaggle_dir, 'kaggle.json')
    if not os.path.exists(api_key_path):
        raise FileNotFoundError(f"Kaggle API key not found. Please place 'kaggle.json' in '{kaggle_dir}'.")

def download_and_extract_datasets():
    datasets_dir = 'datasets'
    os.makedirs(datasets_dir, exist_ok=True)
    hadith_path = os.path.join(datasets_dir, 'all_hadiths_clean.csv')
    quran_path = os.path.join(datasets_dir, 'main_df.csv')
    quran_meta_path = os.path.join(datasets_dir, 'quran.csv')

    if not os.path.exists(hadith_path):
        print("Downloading Hadith dataset...")
        kaggle.api.dataset_download_files('fahd09/hadith-dataset', path=datasets_dir, unzip=True)
    if not os.path.exists(quran_path) or not os.path.exists(quran_meta_path):
        print("Downloading Quran dataset...")
        kaggle.api.dataset_download_files('alizahidraja/quran-nlp', path=datasets_dir, unzip=True)
        # Handle potential nested 'data' directory from Kaggle download
        if os.path.exists(os.path.join(datasets_dir, 'data', 'main_df.csv')):
            os.rename(os.path.join(datasets_dir, 'data', 'main_df.csv'), quran_path)
        if os.path.exists(os.path.join(datasets_dir, 'data', 'quran', 'quran.csv')):
            os.rename(os.path.join(datasets_dir, 'data', 'quran', 'quran.csv'), quran_meta_path)

def load_and_chunk_data():
    print("--- Loading and Processing Data for AI ---")
    check_kaggle_api()
    download_and_extract_datasets()
    quran_loader = CSVLoader(file_path='datasets/main_df.csv', encoding='utf-8')
    hadith_loader = CSVLoader(file_path='datasets/all_hadiths_clean.csv', encoding='utf-8')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    quran_chunks = text_splitter.split_documents(quran_loader.load())
    hadith_chunks = text_splitter.split_documents(hadith_loader.load())
    return quran_chunks, hadith_chunks

def load_quran_for_dictionary():
    """Loads and groups the Quran dataset by Surah for the dictionary view."""
    try:
        df = pd.read_csv('datasets/main_df.csv')
        # Load the supplementary Quran metadata for Arabic names
        quran_meta_df = pd.read_csv('datasets/data/quran/quran.csv')
        
        # Prepare the main data
        df_renamed = df[['EnglishTitle', 'Surah', 'Ayat', 'Arabic', 'Translation - Arthur J']].rename(columns={
            'EnglishTitle': 'surah_name', 'Surah': 'surah_number', 'Ayat': 'ayat_number', 'Arabic': 'arabic_text', 'Translation - Arthur J': 'translation'
        })

        quran_meta_unique = quran_meta_df[['surah_no', 'surah_name']].drop_duplicates()
        quran_meta_renamed = quran_meta_unique.rename(columns={
            'surah_no': 'surah_number', 'surah_name': 'arabic_surah_name'
        })
        
        # Merge the two dataframes
        df_merged = pd.merge(df_renamed, quran_meta_renamed, on='surah_number', how='left')

        # Group verses by Surah
        grouped = df_merged.groupby(['surah_number', 'surah_name', 'arabic_surah_name'])
        surahs_list = []
        for (surah_number, surah_name, arabic_surah_name), group in grouped:
            surah_info = {
                'surah_number': surah_number,
                'surah_name': surah_name,
                'arabic_surah_name': arabic_surah_name,
                'verses': group.to_dict('records')
            }
            surahs_list.append(surah_info)
            
        return surahs_list
    except FileNotFoundError as e:
        print(f"Error loading Quran data: {e}. Please ensure main_df.csv and quran.csv are in the 'datasets' folder.")
        return []

def load_hadith_for_dictionary():
    """Loads and prepares the Hadith dataset as a DataFrame for efficient querying."""
    try:
        df = pd.read_csv('datasets/all_hadiths_clean.csv')
        hadith_data = df[['source', 'chapter_no', 'hadith_no', 'chapter', 'text_ar', 'text_en']].rename(columns={
            'chapter_no': 'chapter_number', 'hadith_no': 'hadith_number', 'text_ar': 'arabic_text', 'text_en': 'english_text'
        }).fillna('Not Available')
        
        # Create slugs for URL routing
        hadith_data['source_slug'] = hadith_data['source'].apply(slugify)
        hadith_data['chapter_slug'] = hadith_data['chapter'].apply(slugify)
        
        return hadith_data
    except FileNotFoundError:
        return pd.DataFrame() # Return an empty DataFrame on error

def get_hadith_sources(df):
    """Returns a list of unique hadith sources with their slugs."""
    if df.empty:
        return []
    sources = df[['source', 'source_slug']].drop_duplicates().sort_values('source')
    return sources.to_dict('records')

def get_chapters_for_source(df, source_slug):
    """Returns a list of chapters for a given source_slug."""
    if df.empty:
        return [], "Unknown"
    
    source_df = df[df['source_slug'] == source_slug]
    if source_df.empty:
        return [], "Unknown"
        
    source_name = source_df.iloc[0]['source']
    chapters = source_df[['chapter', 'chapter_slug', 'chapter_number']].drop_duplicates().sort_values('chapter_number')
    
    return chapters.to_dict('records'), source_name

def get_hadiths_for_chapter(df, source_slug, chapter_slug):
    """Returns all hadiths for a given source and chapter slug."""
    if df.empty:
        return [], "Unknown", "Unknown"
        
    hadiths_df = df[(df['source_slug'] == source_slug) & (df['chapter_slug'] == chapter_slug)]
    if hadiths_df.empty:
        return [], "Unknown", "Unknown"
        
    source_name = hadiths_df.iloc[0]['source']
    chapter_name = hadiths_df.iloc[0]['chapter']
    hadiths = hadiths_df.to_dict('records')
    
    return hadiths, source_name, chapter_name