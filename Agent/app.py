from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
import json
import re

load_dotenv()

import config
import data_pipeline
import vector_store
import crew_setup
from personality import handle_small_talk

app = Flask(__name__)
crew = None
hadith_data_cache = None # This will still store a Pandas DataFrame

# --- Qari List for Murajaah ---
# Keys match the API audio keys ('01', '02', etc.)
QARI_LIST = {
    "01": "Abdullah Al-Juhany",
    "02": "Abdul Muhsin Al-Qasim",
    "03": "Abdurrahman As-Sudais",
    "04": "Ibrahim Al-Dossari",
    "05": "Misyari Rasyid Al-Afasy"
}
# Set a default Qari
DEFAULT_QARI = "05" # Misyari Rasyid Al-Afasy

def initialize_crew():
    """Initializes the crewAI crew if it hasn't been already."""
    global crew
    if crew is None:
        print("--- Initializing Crew for the first time ---")
        retrievers = vector_store.get_milvus_retrievers()
        if retrievers and all(retrievers):
            crew = crew_setup.create_crew(*retrievers)
            print("--- Crew Initialized Successfully ---")
        else:
            print("--- Crew Initialization Failed: Retrievers not available. Run /ingest first. ---")

def get_hadith_df():
    """Helper function to load hadith data into cache if not already present."""
    global hadith_data_cache
    if hadith_data_cache is None:
        print("Loading Hadith data for dictionary...")
        hadith_data_cache = data_pipeline.load_hadith_for_dictionary()
    return hadith_data_cache

@app.route('/')
def chat_page():
    """Renders the main chatbot page."""
    return render_template('chat.html')

@app.route('/quran')
def quran_page():
    """Renders the Quran surah list page."""
    print("Loading Quran surah list...")
    quran_data = data_pipeline.get_quran_surah_list()
    return render_template('quran.html', quran_data=quran_data)

@app.route('/quran/<int:surah_id>')
def quran_detail_page(surah_id):
    """Renders the detail page for a single surah."""
    print(f"Loading detail for Surah {surah_id}...")
    surah_data = data_pipeline.get_quran_surah_detail(surah_id)
    if surah_data is None:
        abort(404)
    return render_template('quran_detail.html', surah=surah_data)

@app.route('/hadith')
def hadith_page():
    """Renders the Hadith sources list."""
    hadith_df = get_hadith_df()
    sources = data_pipeline.get_hadith_sources(hadith_df)
    return render_template('hadith.html', sources=sources)

@app.route('/hadith/<source_slug>')
def hadith_chapters_page(source_slug):
    """Renders the list of chapters for a given Hadith source."""
    hadith_df = get_hadith_df()
    chapters, source_name = data_pipeline.get_chapters_for_source(hadith_df, source_slug)
    if not chapters and source_name == "Unknown":
        abort(404)
    return render_template('hadith_chapters.html', chapters=chapters, source_name=source_name, source_slug=source_slug)

@app.route('/hadith/<source_slug>/<chapter_slug>')
def hadith_list_page(source_slug, chapter_slug):
    """Renders the list of hadiths for a given source and chapter."""
    hadith_df = get_hadith_df()
    hadiths, source_name, chapter_name = data_pipeline.get_hadiths_for_chapter(hadith_df, source_slug, chapter_slug)
    if not hadiths and source_name == "Unknown":
        abort(404)
    return render_template('hadith_list.html', hadith_data=hadiths, source_name=source_name, chapter_name=chapter_name, source_slug=source_slug)

# --- NEW MURAJAAH ROUTES ---

@app.route('/murajaah')
def murajaah_page():
    """Renders the Murajaah selection page (Qari and Surah)."""
    if not data_pipeline.check_connectivity():
        # Render the page with an offline warning
        return render_template('murajaah.html', is_offline=True)
    
    # Fetch surah list for selection
    surah_list = data_pipeline.get_quran_surah_list()
    return render_template('murajaah.html', 
                           is_offline=False, 
                           qari_list=QARI_LIST, 
                           default_qari=DEFAULT_QARI, 
                           surah_list=surah_list)

@app.route('/murajaah/surat/<int:surah_id>')
def murajaah_detail_page(surah_id):
    """Renders the full-text reading page for Murajaah."""
    if not data_pipeline.check_connectivity():
        # Redirect back to selection page if offline
        return render_template('murajaah.html', is_offline=True)
    
    # Get selected Qari from query param, or use default
    qari_key = request.args.get('qari', DEFAULT_QARI)
    if qari_key not in QARI_LIST:
        qari_key = DEFAULT_QARI

    # Fetch the full surah data
    surah_data = data_pipeline.get_quran_surah_detail(surah_id)
    if surah_data is None:
        abort(404)
        
    qari_name = QARI_LIST.get(qari_key, "Unknown Qari")
    
    # Process data for the template
    # Combine all Arabic text into one string, wrapping each ayat in a span
    full_arabic_text = ""
    for ayat in surah_data.get('ayat', []):
        audio_src = ayat.get('audio', {}).get(qari_key, '')
        full_arabic_text += (
            f"<span class='ayat-span' "
            f"data-ayat-number='{ayat.get('nomorAyat')}' "
            f"data-audio-src='{audio_src}'>"
            f"{ayat.get('teksArab')} "
            f"</span>"
        )

    return render_template('murajaah_detail.html', 
                           surah=surah_data, 
                           qari_name=qari_name,
                           full_arabic_text=full_arabic_text)

# --- END NEW MURAJAAH ROUTES ---


@app.route('/ask', methods=['POST'])
def ask_question():
    """Handles chatbot questions."""
    initialize_crew() # Ensure crew is initialized before use
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "'topic' is required."}), 400

    small_talk_response = handle_small_talk(topic)
    if small_talk_response:
        return jsonify(small_talk_response)
    
    if not crew:
        return jsonify({"status": "error", "answer": "Crew not initialized. Please ensure data has been ingested via the /ingest endpoint."}), 500
        
    try:
        result = crew.kickoff(inputs={'topic': topic})
        raw_output = result.raw
        cleaned_output = raw_output.strip().replace('```json', '').replace('```', '').strip()
        answer_dict = json.loads(cleaned_output)
        return jsonify(answer_dict)
    except Exception as e:
        return jsonify({"status": "error", "answer": f"An unexpected error occurred: {e}"}), 500

@app.route('/ingest')
def ingest():
    """One-time endpoint for data ingestion."""
    try:
        quran_chunks, hadith_chunks = data_pipeline.load_and_chunk_data()
        vector_store.ingest_data_to_milvus(config.QURAN_COLLECTION, quran_chunks)
        vector_store.ingest_data_to_milvus(config.HADITH_COLLECTION, hadith_chunks)
        return "Data ingestion complete!", 200
    except Exception as e:
        return f"An error occurred during ingestion: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)