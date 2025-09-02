from flask import Flask, render_template, request, jsonify
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
        print("First time setup: Initializing Crew")
        quran_retriever, hadith_retriever = vector_store.get_milvus_retrievers()
        if quran_retriever and hadith_retriever:
            crew = crew_setup.create_crew(quran_retriever, hadith_retriever)
            print("Crew Initialized Successfully")
        else:
            print("Crew Initialization Failed")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "Invalid request. 'topic' is required."}), 400
    if not crew:
        return jsonify({"error": "Crew not initialized. Please ensure data has been ingested via the /ingest endpoint."}), 500

    try:
        result = crew.kickoff(inputs={'topic': topic})
        return jsonify({"answer": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ingest')
def ingest():
    """One-time endpoint to trigger data download and ingestion into Milvus."""
    try:
        quran_chunks, hadith_chunks = data_pipeline.load_and_chunk_data()
        if not quran_chunks or not hadith_chunks:
            return "Failed to load data. Check CSV file paths and Kaggle setup.", 500

        vector_store.ingest_data_to_milvus(config.QURAN_COLLECTION, quran_chunks)
        vector_store.ingest_data_to_milvus(config.HADITH_COLLECTION, hadith_chunks)
        return "Data ingestion complete! You can now use the main application.", 200
    except Exception as e:
        return f"An error occurred during ingestion: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)