import string
from pythainlp import word_tokenize
from pythainlp.corpus import thai_stopwords
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from mineru_client import MinerUClient
import requests
import zipfile
import io
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
                                                                                                                                                                       
STOP_WORDS = {                                                                                                                                                         
    "a", "an", "the", "and", "or", "but", "is", "am", "are",                                                                                                           
    "was", "were", "in", "on", "at", "to", "for", "of", "with",                                                                                                        
    "it", "this", "that", "i", "you", "he", "she", "we", "they",                                                                                                       
    "be", "been", "as", "just"                                                                                                                                      
}                                                                                                                                                                      
THAI_STOP_WORDS = thai_stopwords()
ALLSTOPWORDS = STOP_WORDS.union(THAI_STOP_WORDS)

def simple_stemmer(word):                                                                                                                                              
    if word.endswith('s') and len(word) > 3: word = word[:-1]                                                                                                          
    if word.endswith('ing') and len(word) > 4: word = word[:-3]                                                                                                        
    if word.endswith('ed') and len(word) > 4: word = word[:-2]                                                                                                         
                                                                                                                                                                       
    return word
                                                                                                                                                                       
def clean_text(text):
    text = text.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    words = word_tokenize(text, engine="newmm", keep_whitespace=False)                                                                                                                                              
    process_word = []
    for w in words:  
        w = w.lower().strip()                                                                                                                                               
        if w not in ALLSTOPWORDS and len(w) > 1:                                                                                                                                        
            process_word.append(simple_stemmer(w))                                                                                                                     
    return process_word                                                                                                                                                
                                                                                                                                                                       

def get_tfidf_similarity(text1, text2):
    tokens1 = clean_text(text1)
    tokens2 = clean_text(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
        
    str1 = " ".join(tokens1)
    str2 = " ".join(tokens2)
    
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([str1, str2])
        sim_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(sim_score)
    except ValueError:
        return 0.0


def fix_thai_pdf_text(t):
    if not t: return ""
    # Fix SARA AM (e.g., "ส ำ" -> "สำ")
    t = re.sub(r'([ก-ฮ])\s+(ำ)', r'\1\2', t)
    # Fix floating vowels/tones (e.g., "ฝึ ก" -> "ฝึก", "น้ ี" -> "นี้")
    t = re.sub(r'([ก-ฮ])\s+([ัิีึืฺุู็่้๊๋์])', r'\1\2', t)
    # Fix SARA AA (e.g., "ก า" -> "กา")
    t = re.sub(r'([ก-ฮ])\s+(า)', r'\1\2', t)
    return t

def extract_text_from_url(url, api_key):
    # Initialize MinerU Client
    if not api_key:
        return "Error: MinerU API Key is missing."
    
    client = MinerUClient(api_key)
    
    try:
        # 1. Submit URL Task
        task_id = client.extract(url)
        
        # 2. Poll
        result = client.poll_task(task_id)
        
        # 3. Handle Result
        if 'full_zip_url' in result:
            r = requests.get(result['full_zip_url'])
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    # Find the markdown file
                    md_files = [f for f in z.namelist() if f.endswith('.md')]
                    if md_files:
                        with z.open(md_files[0]) as f:
                            content = f.read().decode('utf-8')
                            return fix_thai_pdf_text(content)
                    else:
                        return f"Error: No markdown file found in zip. Files: {z.namelist()}"
            else:
                 return f"Error downloading result zip: Status {r.status_code}"

        elif 'full_text' in result:
             return fix_thai_pdf_text(result['full_text'])
        
        # Fallback
        text = result.get('full_text') or result.get('markdown') or result.get('text')
        if not text:
             return f"Error: No text found in MinerU response. Data: {str(result)[:100]}"
             
        return fix_thai_pdf_text(text)

    except Exception as e:
        return f"Error extracting from URL: {str(e)}"


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text1 = ""
    text2 = ""

    # Check for text in form or json
    if 'text1' in request.form:
        text1 = request.form['text1']
    elif request.json and 'text1' in request.json:
        text1 = request.json['text1']

    if 'text2' in request.form:
        text2 = request.form['text2']
    elif request.json and 'text2' in request.json:
        text2 = request.json['text2']
    
    similarity = get_tfidf_similarity(text1, text2)
    
    return jsonify({
        'similarity': similarity * 100,
        'message': 'Calculation Success'
    })

@app.route('/extract_text', methods=['POST'])
def extract_text():
    # Expecting URL and API Key
    if 'url' not in request.form or request.form['url'].strip() == '':
        return jsonify({'error': 'No URL provided'}), 400
        
    if 'api_key' not in request.form or request.form['api_key'].strip() == '':
        return jsonify({'error': 'No API key provided'}), 400

    url = request.form['url'].strip()
    api_key = request.form['api_key'].strip()
    
    try:
        text = extract_text_from_url(url, api_key)
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)                                                                                                                      
