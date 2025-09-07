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

@app.before_request
def initialize():
    """Initializes the crew once before the first request."""
    global crew
    if crew is None and request.endpoint not in ['ingest', 'static']:
        print("--- First time setup: Initializing Crew ---")
        retrievers = vector_store.get_milvus_retrievers()
        if retrievers and all(retrievers):
            crew = crew_setup.create_crew(*retrievers)
            print("--- Crew Initialized Successfully ---")
        else:
            print("--- Crew Initialization Failed: Retrievers not available. ---")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "'topic' is required."}), 400

    small_talk_response = handle_small_talk(topic)
    if small_talk_response:
        print("Handling request as small talk.")
        return jsonify(small_talk_response)
    
    if not crew:
        return jsonify({"status": "error", "answer": "Crew not initialized. Please ensure data has been ingested via the /ingest endpoint."}), 500
        
    try:
        print("Passing request to AI Crew...")
        result = crew.kickoff(inputs={'topic': topic})
        
        # Ensure the final output is always a parsable JSON
        raw_output = result.raw
        
        # Clean the output string: remove markdown backticks and the word "json"
        cleaned_output = raw_output.strip().replace('```json', '').replace('```', '').strip()
        
        answer_dict = json.loads(cleaned_output)
        return jsonify(answer_dict)

    except json.JSONDecodeError:
        # If parsing fails, wrap the raw text in our standard error format
        print(f"JSONDecodeError: Could not parse the crew's output: {raw_output}")
        return jsonify({"status": "error", "answer": "The AI response was not in a valid format. Please try rephrasing your question."})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "answer": f"An unexpected error occurred: {e}"}), 500

@app.route('/ingest')
def ingest():
    """One-time endpoint for data download and ingestion."""
    try:
        quran_chunks, hadith_chunks = data_pipeline.load_and_chunk_data()
        if not quran_chunks or not hadith_chunks:
            return "Failed to load/chunk data.", 500
        vector_store.ingest_data_to_milvus(config.QURAN_COLLECTION, quran_chunks)
        vector_store.ingest_data_to_milvus(config.HADITH_COLLECTION, hadith_chunks)
        return "Data ingestion complete!", 200
    except Exception as e:
        error_message = f"An error occurred during ingestion: {type(e).__name__} - {e}"
        print(error_message)
        return error_message, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)