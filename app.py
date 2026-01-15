import os
import uuid
import shutil
import random
import tempfile
from flask import Flask, render_template, request, send_from_directory, jsonify, send_file
from werkzeug.utils import secure_filename

# --- IMPORTS CONVERSION ---
import img2pdf
import aspose.words as aw
import aspose.slides as slides
import aspose.pdf as ap
from pdf2docx import Converter
from xhtml2pdf import pisa

app = Flask(__name__)

# --- CONFIGURATION DOSSIERS ---
# On utilise des chemins relatifs pour Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')

# Création des dossiers au démarrage et nettoyage
for folder in [UPLOAD_FOLDER, EXPORT_FOLDER]:
    if os.path.exists(folder):
        shutil.rmtree(folder) # Nettoie les restes des sessions précédentes
    os.makedirs(folder, exist_ok=True)

# --- ROUTES DE NAVIGATION ---

@app.route('/')
def index():
    # NKonvert est la page d'accueil
    return render_template('index.html')

@app.route('/boost')
def boost_page():
    return render_template('motivation.html')

@app.route('/zip')
def zip_page():
    return render_template('zip.html')

# --- LOGIQUE 1 : NKONVERT (Conversion) ---

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier envoyé"}), 400
    
    file = request.files['file']
    target_format = request.form.get('target_format')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "Fichier vide"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}{ext}")
    output_filename = f"{unique_id}.{target_format}"
    output_path = os.path.join(EXPORT_FOLDER, output_filename)

    file.save(input_path)

    try:
        # PPTX vers PDF
        if ext == '.pptx' and target_format == 'pdf':
            pres = slides.Presentation(input_path)
            pres.save(output_path, slides.export.SaveFormat.PDF)

        # PDF vers PPTX
        elif ext == '.pdf' and target_format == 'pptx':
            doc = ap.Document(input_path)
            doc.save(output_path, ap.PptxSaveOptions())
        
        # PDF vers DOCX
        elif ext == '.pdf' and target_format == 'docx':
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
        
        # DOCX vers PDF
        elif ext == '.docx' and target_format == 'pdf':
            doc = aw.Document(input_path)
            doc.save(output_path)

        # IMAGES vers PDF
        elif ext in ['.jpg', '.png', '.jpeg'] and target_format == 'pdf':
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(input_path))
                
        else:
            return jsonify({"success": False, "error": "Format non supporté"}), 400

        return jsonify({"success": True, "download_url": f"/download_file/{output_filename}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- LOGIQUE 2 : BOOST SPIRIT (Motivation) ---

@app.route('/generate_ajax', methods=['POST'])
def generate_boost():
    prenom = request.form.get('prenom', 'Aventurier')
    nom = request.form.get('nom', '')
    
    sujets = ["L'avenir", "Le succès", "La réussite", "Le destin", "La persévérance", "L'audace"]
    actions = ["appartient à ceux qui", "se construit par ceux qui", "sourit à ceux qui", "récompense ceux qui"]
    finalites = ["n'abandonnent jamais.", "osent sortir de leur zone de confort.", "travaillent avec passion.", "voient des opportunités partout."]
    
    phrase = f"{random.choice(sujets)} {random.choice(actions)} {random.choice(finalites)}"
    
    return jsonify({
        "status": "success",
        "phrase": phrase,
        "username": f"{prenom} {nom}"
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

