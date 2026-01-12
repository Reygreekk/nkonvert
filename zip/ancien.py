import os
import shutil
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration des dossiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'exports')

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/zip_folder', methods=['POST'])
def zip_folder():
    # On récupère la liste des fichiers envoyés
    uploaded_files = request.files.getlist('files')
    
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"success": False, "error": "Aucun fichier reçu."}), 400

    try:
        # 1. Créer un répertoire temporaire pour stocker les fichiers reçus
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # Nom du dossier racine (extrait du chemin relatif du premier fichier)
            # Exemple: "MonDossier/image.png" -> "MonDossier"
            root_folder_name = uploaded_files[0].filename.split('/')[0]
            if not root_folder_name:
                root_folder_name = "archive_upload"

            # 2. Enregistrer chaque fichier en respectant sa structure de dossiers
            for file in uploaded_files:
                # Le filename contient le chemin relatif (ex: dossier/sous-dossier/fic.txt)
                relative_path = file.filename
                
                # Création du chemin complet localement dans le dossier temp
                full_path = os.path.join(temp_dir, relative_path)
                
                # Créer les sous-dossiers si nécessaire
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Sauvegarder le fichier
                file.save(full_path)

            # 3. Préparer le nom du ZIP final
            zip_filename = f"{root_folder_name}_archive"
            zip_dest_path = os.path.join(OUTPUT_DIR, zip_filename)

            # 4. Compresser le contenu du dossier temporaire
            # On compresse le dossier qui se trouve à l'intérieur de temp_dir
            source_to_zip = os.path.join(temp_dir, root_folder_name)
            shutil.make_archive(zip_dest_path, 'zip', source_to_zip)
            
            return jsonify({
                "success": True, 
                "message": f"Dossier '{root_folder_name}' compressé avec succès !",
                "download_url": f"/download/{zip_filename}.zip"
            })

    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"success": False, "error": "Fichier introuvable."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2500, debug=True)