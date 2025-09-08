from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import json

load_dotenv()

import config
import data_pipeline
import vector_store
import crew_setup
from personality import handle_small_talk

app = Flask(__name__)
crew = None
quran_data_cache = None
hadith_data_cache = None

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
    """Renders the Hadith dictionary page."""
    global hadith_data_cache
    if hadith_data_cache is None:
        print("Loading Hadith data for dictionary...")
        hadith_data_cache = data_pipeline.load_hadith_for_dictionary()
    return render_template('hadith.html', hadith_data=hadith_data_cache)

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