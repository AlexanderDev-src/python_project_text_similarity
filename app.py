import math                                                                                                                                                            
import string                                                                                                                                                          
from collections import Counter                                                                                                                                        
import tkinter as tk                                                                                                                                                   
from tkinter import scrolledtext, messagebox, filedialog                                                                                                               
from pypdf import PdfReader                                                                                                                                            
import customtkinter as ctk                                                                                                                                            
from pythainlp import word_tokenize
from pythainlp.corpus import thai_stopwords
from flask import Flask, render_template, request, jsonify
                                                                                                                                                                       
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
                                                                                                                                                                       
def get_jaccard_similarity(text1, text2, n=2):                                                                                                                               
                      
    tokens1 = clean_text(text1)
    tokens2 = clean_text(text2)

    if len(tokens1) < n or len(tokens2) < n:
        set1 = set(tokens1)
        set2 = set(tokens2)

    else:
        set1 = set(tuple(tokens1[i:i+n]) for i in range(len(tokens1)-n+1))
        set2 = set(tuple(tokens2[i:i+n]) for i in range(len(tokens2)-n+1))


    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    if union == 0 :
        return 0.0
    
    return intersection / union
                                                                                                                                                                       
def extract_text_from_pdf(file_source):
    text = ""
    try:
        # file_source can be a file path or a file-like object
        reader = PdfReader(file_source)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text1 = ""
    text2 = ""

    # Check for files
    if 'file1' in request.files and request.files['file1'].filename != '':
        text1 = extract_text_from_pdf(request.files['file1'])
    elif 'text1' in request.form:
        text1 = request.form['text1']
    elif request.json and 'text1' in request.json:
        text1 = request.json['text1']

    if 'file2' in request.files and request.files['file2'].filename != '':
        text2 = extract_text_from_pdf(request.files['file2'])
    elif 'text2' in request.form:
        text2 = request.form['text2']
    elif request.json and 'text2' in request.json:
        text2 = request.json['text2']
    
    similarity = get_jaccard_similarity(text1, text2, n=2)
    
    return jsonify({
        'similarity': similarity * 100,
        'message': 'Calculation Success'
    })

@app.route('/extract_text', methods=['POST'])
def extract_text():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        text = extract_text_from_pdf(file)
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)                                                                                                                      
