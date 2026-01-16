import os
import uuid
import shutil
import random
import time
import base64
import tempfile
from io import BytesIO
from datetime import timedelta
# Import obligatoire pour l'Oracle
from flask import Flask, render_template, request, send_from_directory, jsonify, session
from werkzeug.utils import secure_filename
from PIL import Image
# --- BIBLIOTHÈQUES ---
import img2pdf
import mammoth
import fitz  # PyMuPDF
from docx import Document
from pdf2image import convert_from_path
from xhtml2pdf import pisa
from striprtf.striprtf import rtf_to_text
from fpdf import FPDF
app = Flask(__name__)
# --- CONFIGURATION SESSION ---
app.secret_key = "nkonvert_oracle_secret_key_2026"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
for folder in [UPLOAD_FOLDER, EXPORT_FOLDER]:
    os.makedirs(folder, exist_ok=True)
def cleanup_old_files():
    """Supprime les fichiers de plus de 10 minutes"""
    now = time.time()
    for folder in [UPLOAD_FOLDER, EXPORT_FOLDER]:
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.stat(path).st_mtime < now - 600:
                try:
                    os.remove(path)
                except:
                    pass

# --- ROUTES NAVIGATION ---
@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/boost')
def boost_page(): 
    return render_template('motivation.html')

@app.route('/zip')
def zip_page(): 
    return render_template('zip.html')

# --- LOGIQUE DE CONVERSION ---
@app.route('/convert', methods=['POST'])
def convert():
    cleanup_old_files()
    if 'file' not in request.files: 
        return jsonify({"success": False, "error": "Aucun fichier envoyé"}), 400
    
    file = request.files['file']
    target_format = request.form.get('target_format')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "Nom de fichier vide"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}{ext}")
    output_filename = f"{unique_id}.{target_format}"
    output_path = os.path.join(EXPORT_FOLDER, output_filename)
    
    file.save(input_path)

    try:
        # 1. WORD (.docx) vers PDF
        if ext == '.docx' and target_format == 'pdf':
            with open(input_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value 
            with open(output_path, "wb") as pdf_file:
                pisa.CreatePDF(html_content, dest=pdf_file)

        # 2. PDF vers WORD (.docx)
        elif ext == '.pdf' and target_format == 'docx':
            doc_pdf = fitz.open(input_path)
            doc_word = Document()
            for page in doc_pdf:
                doc_word.add_paragraph(page.get_text())
            doc_word.save(output_path)
            doc_pdf.close()

        # 3. IMAGES vers PDF
        elif ext in ['.jpg', '.jpeg', '.png'] and target_format == 'pdf':
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(input_path))

        # 4. PDF vers IMAGE (PNG/JPG)
        elif ext == '.pdf' and target_format in ['png', 'jpg']:
            images = convert_from_path(input_path, first_page=1, last_page=1)
            images[0].save(output_path, target_format.upper())

        # 5. HTML vers PDF
        elif ext == '.html' and target_format == 'pdf':
            with open(input_path, "r", encoding="utf-8") as hf:
                source_html = hf.read()
            with open(output_path, "wb") as pf:
                pisa.CreatePDF(source_html, dest=pf)

        # 6. IMAGE vers SVG
        elif ext in ['.jpg', '.jpeg', '.png'] and target_format == 'svg':
            with Image.open(input_path) as img:
                width, height = img.size
                buffered = BytesIO()
                img.save(buffered, format=img.format)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                svg_data = f'<?xml version="1.0" encoding="UTF-8"?><svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"><image width="{width}" height="{height}" href="data:image/{img.format.lower()};base64,{img_str}"/></svg>'
                with open(output_path, "w") as svg_file:
                    svg_file.write(svg_data)

        else:
            return jsonify({"success": False, "error": "Format non supporté"}), 400

        return jsonify({"success": True, "download_url": f"/download_file/{output_filename}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
# --- LOGIQUE 2 : BOOST SPIRIT (Oracle) ---
@app.route('/generate_ajax', methods=['POST'])
def generate_boost():
    session.permanent = True
    prenom = request.form.get('prenom', '').strip()
    nom = request.form.get('nom', '').strip()
    identite = f"{prenom} {nom}".strip() or "Aventurier"
    
    if 'counter' not in session: session['counter'] = 1
    else: session['counter'] += 1
    compteur = session['counter']

   # --- SÉLECTION DE L'INTRO ---
    if compteur == 1:
        intro = f"Bonjour {identite}... J'espère que ta journée se déroule bien jusque-là. Voici ton message boost :"
    elif 1 < compteur <= 12:
        intro = random.choice([
            f"Je vois que tu apprécies l'énergie, {prenom or 'ami'}.",
            "On ne s'arrête plus ! Voici encore pour toi :",
            "Voici encore une parole pour toi et te faire du bien :"
        ])
    else:
        intro = random.choice([
            "Dis donc, tu as pris un abonnement ?",
            "On dirait que tu cherches le bon conseil...",
            f"Je wanda seulement sur toi {prenom or 'ami'}...",
            "Tu n'as pas un travail qui t'attend ? Voici ta dose :"
        ])

    branches = {
        "Confiance": {
            "sujets": ["Ta valeur", "Ta lumière", "Ta force"],
            "actions": ["est une énergie qui va", "te donne le pouvoir de"],
            "finalites": ["réaliser l'impossible.", "transformer tes rêves."]
        },
        "Espoir": {
            "sujets": ["Ta douleur", "Ton combat"],
            "actions": ["te prépare à", "ouvrira sur"],
            "finalites": ["une aube radieuse.", "une paix durable."]
        },
        "Comique": {
            "sujets": ["Sache que si tu dors,"],
            "actions": ["ta vie"],
            "finalites": ["dort aussi, réveille-toi !", "Dort ohhh, je t'ai prévenu."]
        }
    }

    selected_branch = random.choice(list(branches.keys()))
    data = branches[selected_branch]
    phrase = f"{random.choice(data['sujets'])} {random.choice(data['actions'])} {random.choice(data['finalites'])}"
    
    return jsonify({
        "status": "success",
        "intro": intro,
        "phrase": phrase,
        "compteur": compteur,
        "type": selected_branch
    })

# --- LOGIQUE 3 : ZIP TOOL (Compression) ---

@app.route('/zip_folder', methods=['POST'])
def zip_folder():
    if 'files' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier reçu."}), 400

    uploaded_files = request.files.getlist('files')
    unique_id = str(uuid.uuid4())[:8]
    zip_filename = f"nkalas_archive_{unique_id}"
    zip_dest_path = os.path.join(EXPORT_FOLDER, zip_filename)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            for file in uploaded_files:
                rel_path = file.filename
                full_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)

            # On compresse le dossier temporaire
            shutil.make_archive(zip_dest_path, 'zip', temp_dir)
            
        return jsonify({
            "success": True, 
            "download_url": f"/download_file/{zip_filename}.zip"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- GESTIONNAIRE DE TÉLÉCHARGEMENT UNIQUE ---

@app.route('/download_file/<filename>')
def download_file(filename):
    # Sécurité pour éviter de sortir du dossier export
    safe_name = secure_filename(filename)
    return send_from_directory(EXPORT_FOLDER, safe_name, as_attachment=True)

# --- LANCEMENT ---

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)














