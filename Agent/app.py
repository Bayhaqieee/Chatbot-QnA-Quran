from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
import json
import re
import random

load_dotenv()

import config
import data_pipeline
import vector_store
import crew_setup
from personality import handle_small_talk

app = Flask(__name__)
crew = None
hadith_data_cache = None 

# --- Qari Data ---
QARI_LIST = {
    "01": {"name": "Abdullah Al-Juhany", "image": "src/image/abdullah-al-juhany.jpg"},
    "02": {"name": "Abdul Muhsin Al-Qasim", "image": "src/image/Abdul_Mohsin_Al-Qasim.jpg"},
    "03": {"name": "Abdurrahman As-Sudais", "image": "src/image/Abdul-Rahman-Al-Sudais.jpg"},
    "04": {"name": "Ibrahim Al-Dossari", "image": "src/image/ibrahim-al-dosari.png"},
    "05": {"name": "Misyari Rasyid Al-Afasy", "image": "src/image/misyari-rasyid-al-afasy.jpeg"}
}

# Mapping IDs to API URL Slugs for Audio
QARI_SLUGS = {
    "01": "Abdullah-Al-Juhany",
    "02": "Abdul-Muhsin-Al-Qasim",
    "03": "Abdurrahman-as-Sudais",
    "04": "Ibrahim-Al-Dossari",
    "05": "Misyari-Rasyid-Al-Afasi"
}

DEFAULT_QARI = "05" 

# --- HELPER FUNCTIONS ---
def to_eastern_arabic_numerals(number):
    """Converts a standard integer to Eastern Arabic numerals."""
    eastern_numerals = '٠١٢٣٤٥٦٧٨٩'
    return ''.join(eastern_numerals[int(digit)] for digit in str(number))

def initialize_crew():
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
    global hadith_data_cache
    if hadith_data_cache is None:
        print("Loading Hadith data for dictionary...")
        hadith_data_cache = data_pipeline.load_hadith_for_dictionary()
    return hadith_data_cache

# --- ROUTES ---

@app.route('/')
def chat_page():
    return render_template('chat.html')

@app.route('/quran')
def quran_page():
    quran_data = data_pipeline.get_quran_surah_list()
    return render_template('quran.html', quran_data=quran_data)

@app.route('/quran/<int:surah_id>')
def quran_detail_page(surah_id):
    surah_data = data_pipeline.get_quran_surah_detail(surah_id)
    if surah_data is None:
        abort(404)
    return render_template('quran_detail.html', surah=surah_data)

@app.route('/hadith')
def hadith_page():
    hadith_df = get_hadith_df()
    sources = data_pipeline.get_hadith_sources(hadith_df)
    return render_template('hadith.html', sources=sources)

@app.route('/hadith/<source_slug>')
def hadith_chapters_page(source_slug):
    hadith_df = get_hadith_df()
    chapters, source_name = data_pipeline.get_chapters_for_source(hadith_df, source_slug)
    if not chapters and source_name == "Unknown":
        abort(404)
    return render_template('hadith_chapters.html', chapters=chapters, source_name=source_name, source_slug=source_slug)

@app.route('/hadith/<source_slug>/<chapter_slug>')
def hadith_list_page(source_slug, chapter_slug):
    hadith_df = get_hadith_df()
    hadiths, source_name, chapter_name = data_pipeline.get_hadiths_for_chapter(hadith_df, source_slug, chapter_slug)
    if not hadiths and source_name == "Unknown":
        abort(404)
    return render_template('hadith_list.html', hadith_data=hadiths, source_name=source_name, chapter_name=chapter_name, source_slug=source_slug)

@app.route('/murajaah')
def murajaah_page():
    if not data_pipeline.check_connectivity():
        return render_template('murajaah.html', is_offline=True)
    
    surah_list = data_pipeline.get_quran_surah_list()
    return render_template('murajaah.html', 
                           is_offline=False, 
                           qari_list=QARI_LIST, 
                           default_qari=DEFAULT_QARI, 
                           surah_list=surah_list)

@app.route('/murajaah/surat/<int:surah_id>')
def murajaah_detail_page(surah_id):
    if not data_pipeline.check_connectivity():
        return render_template('murajaah.html', is_offline=True)
    
    qari_key = request.args.get('qari', DEFAULT_QARI)
    if qari_key not in QARI_LIST:
        qari_key = DEFAULT_QARI

    surah_data = data_pipeline.get_quran_surah_detail(surah_id)
    if surah_data is None:
        abort(404)
        
    qari_name = QARI_LIST.get(qari_key, {}).get("name", "Unknown Qari")
    next_surah_id = surah_id + 1 if surah_id < 114 else 1
    
    full_arabic_text = ""
    for ayat in surah_data.get('ayat', []):
        audio_src = ayat.get('audio', {}).get(qari_key, '')
        ayat_number = ayat.get('nomorAyat')
        arabic_number = to_eastern_arabic_numerals(ayat_number)
        
        full_arabic_text += (
            f"<span class='ayat-span' "
            f"data-ayat-number='{ayat_number}' "
            f"data-audio-src='{audio_src}'>"
            f"{ayat.get('teksArab')}" 
            f"</span>"
            f" <span class='murajaah-separator'>\u06dd{arabic_number}</span> "
        )

    return render_template('murajaah_detail.html', 
                           surah=surah_data, 
                           qari_name=qari_name,
                           full_arabic_text=full_arabic_text,
                           next_surah_id=next_surah_id,
                           current_qari=qari_key)

# --- GAME ROUTES ---

@app.route('/game')
def game_page():
    """Renders the Game menu page."""
    if not data_pipeline.check_connectivity():
         return render_template('game.html', is_offline=True)
    
    surah_list = data_pipeline.get_quran_surah_list()
    return render_template('game.html', 
                           is_offline=False,
                           surah_list=surah_list,
                           qari_list=QARI_LIST,
                           default_qari=DEFAULT_QARI)

@app.route('/game/ayat/play')
def game_ayat_play():
    """Renders the gameplay interface."""
    if not data_pipeline.check_connectivity():
        return render_template('game.html', is_offline=True)
    return render_template('game_play.html')

@app.route('/api/game/generate', methods=['POST'])
def generate_game_data():
    """Generates random questions for the Ayat Guesser game."""
    try:
        data = request.json
        surah_target = data.get('surah') # 'all' or surah_id
        qari_id = data.get('qari')
        amount = int(data.get('amount', 5))

        surah_list = data_pipeline.get_quran_surah_list() # Need this for max ayat info
        questions = []

        for _ in range(amount):
            # 1. Pick a Target Surah
            if surah_target == 'all':
                target_surah_info = random.choice(surah_list)
            else:
                target_surah_info = next((s for s in surah_list if str(s['nomor']) == str(surah_target)), None)
                if not target_surah_info: continue 
            
            target_surah_no = target_surah_info['nomor']
            max_ayat = target_surah_info['jumlahAyat']
            
            # 2. Pick a Target Ayat
            target_ayat_no = random.randint(1, max_ayat)
            
            # 3. Construct Audio URL
            qari_slug = QARI_SLUGS.get(qari_id, "Misyari-Rasyid-Al-Afasi")
            surah_pad = f"{target_surah_no:03d}"
            ayat_pad = f"{target_ayat_no:03d}"
            audio_url = f"https://cdn.equran.id/audio-partial/{qari_slug}/{surah_pad}{ayat_pad}.mp3"

            # 4. Generate Options (1 Correct + 3 Wrong)
            correct_answer = f"{target_surah_info['namaLatin']} : {target_ayat_no}"
            options = [correct_answer]
            
            while len(options) < 4:
                if surah_target == 'all':
                    # If playing "All Surah", pick random surah and random ayat
                    wrong_surah = random.choice(surah_list)
                    wrong_ayat = random.randint(1, wrong_surah['jumlahAyat'])
                    wrong_option = f"{wrong_surah['namaLatin']} : {wrong_ayat}"
                else:
                    # If playing specific Surah, pick same surah but different ayat
                    wrong_ayat = random.randint(1, max_ayat)
                    # Ensure we don't pick the target ayat again (though unlikely to match exact correct_answer string)
                    while wrong_ayat == target_ayat_no:
                        wrong_ayat = random.randint(1, max_ayat)
                    wrong_option = f"{target_surah_info['namaLatin']} : {wrong_ayat}"
                
                if wrong_option not in options:
                    options.append(wrong_option)
            
            random.shuffle(options)
            
            questions.append({
                "audio": audio_url,
                "correct": correct_answer,
                "options": options,
                "surah_name": target_surah_info['namaLatin'],
                "ayat_number": target_ayat_no
            })
            
        return jsonify(questions)

    except Exception as e:
        print(f"Game Generation Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask_question():
    initialize_crew()
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "'topic' is required."}), 400

    small_talk_response = handle_small_talk(topic)
    if small_talk_response:
        return jsonify(small_talk_response)
    
    if not crew:
        return jsonify({"status": "error", "answer": "Crew not initialized."}), 500
        
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
    try:
        quran_chunks, hadith_chunks = data_pipeline.load_and_chunk_data()
        vector_store.ingest_data_to_milvus(config.QURAN_COLLECTION, quran_chunks)
        vector_store.ingest_data_to_milvus(config.HADITH_COLLECTION, hadith_chunks)
        return "Data ingestion complete!", 200
    except Exception as e:
        return f"An error occurred during ingestion: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)