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
quran_data_cache = None
hadith_data_cache = None # This will now store a Pandas DataFrame

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
    """Renders the Quran dictionary page."""
    global quran_data_cache
    if quran_data_cache is None:
        print("Loading Quran data for dictionary...")
        quran_data_cache = data_pipeline.load_quran_for_dictionary()
    return render_template('quran.html', quran_data=quran_data_cache)

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