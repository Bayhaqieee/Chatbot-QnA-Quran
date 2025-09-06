from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import json

load_dotenv()

import config
import data_pipeline
import vector_store
import crew_setup

app = Flask(__name__)
crew = None

@app.before_request
def initialize():
    """Initializes the crew once before the first request."""
    global crew
    if crew is None and request.endpoint not in ['ingest', 'static']:
        print("First time setup: Initializing Crew ")
        retrievers = vector_store.get_milvus_retrievers()
        if retrievers and all(retrievers):
            crew = crew_setup.create_crew(*retrievers)
            print("Crew Initialized Successfully ")
        else:
            print("Crew Initialization Failed: Retrievers not available. ")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "'topic' is required."}), 400
    if not crew:
        return jsonify({"error": "Crew not ready. Please ingest data via the /ingest endpoint."}), 500
    try:
        # The result is a CrewOutput object, not a simple string
        result = crew.kickoff(inputs={'topic': topic})

        # The raw output from the last agent is in the .raw attribute
        # We instructed this agent to produce a JSON string.
        raw_json_output = result.raw
        
        try:
            # Parse the string into a dictionary to send as proper JSON
            answer_dict = json.loads(raw_json_output)
            return jsonify(answer_dict)
        except json.JSONDecodeError:
            # Fallback if the agent fails to produce perfect JSON
            return jsonify({"status": "error", "answer": raw_json_output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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