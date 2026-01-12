import os
import shutil
import tempfile
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# En ligne, on utilise souvent /tmp pour le stockage temporaire ou un dossier relatif
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'exports')

# Création sécurisée du dossier de sortie
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/zip_folder', methods=['POST'])
def zip_folder():
    if 'files' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier reçu."}), 400

    uploaded_files = request.files.getlist('files')
    
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"success": False, "error": "Liste de fichiers vide."}), 400

    try:
        # Utilisation de tempfile pour ne pas polluer le disque du serveur
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # Récupération du nom du dossier d'origine
            first_path = uploaded_files[0].filename
            root_folder_name = first_path.split('/')[0] if '/' in first_path else "archive"
            
            # On nettoie le nom pour éviter les injections de chemin (sécurité en ligne)
            safe_root_name = secure_filename(root_folder_name)

            for file in uploaded_files:
                # On recrée la structure de sous-dossiers
                # On s'assure que le chemin est relatif pour éviter d'écrire hors du temp_dir
                rel_path = file.filename
                full_path = os.path.join(temp_dir, rel_path)
                
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                file.save(full_path)

            # Création d'un identifiant unique pour éviter que deux utilisateurs 
            # téléchargent le fichier l'un de l'autre au même moment
            unique_id = str(uuid.uuid4())[:8]
            zip_filename = f"{safe_root_name}_{unique_id}"
            zip_dest_path = os.path.join(OUTPUT_DIR, zip_filename)

            # Compression du contenu
            source_to_zip = os.path.join(temp_dir, root_folder_name)
            # Si le dossier racine n'existe pas dans le temp (cas fichiers seuls)
            if not os.path.exists(source_to_zip):
                source_to_zip = temp_dir

            shutil.make_archive(zip_dest_path, 'zip', source_to_zip)
            
            return jsonify({
                "success": True, 
                "message": "Compression terminée !",
                "download_url": f"/download/{zip_filename}.zip"
            })

    except Exception as e:
        app.logger.error(f"Erreur Serveur: {e}")
        return jsonify({"success": False, "error": "Erreur interne lors de la compression."}), 500

@app.route('/download/<filename>')
def download(filename):
    # Sécurité: on empêche l'accès à d'autres dossiers avec secure_filename
    safe_name = secure_filename(filename)
    file_path = os.path.join(OUTPUT_DIR, safe_name)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"success": False, "error": "Fichier expiré ou introuvable."}), 404

if __name__ == '__main__':
    # CONFIGURATION EN LIGNE :
    # On récupère le port via la variable d'environnement (nécessaire pour Heroku/Render)
    # Si non défini, on utilise 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)