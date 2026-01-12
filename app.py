from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import uuid
import img2pdf
from pdf2docx import Converter
from docx2pdf import convert as d2p
from xhtml2pdf import pisa  # Remplacement de WeasyPrint
import comtypes.client 
import aspose.pdf as ap  

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400
    
    file = request.files['file']
    target_format = request.form.get('target_format')
    
    if file.filename == '':
        return jsonify({"error": "Fichier vide"}), 400

    # Création d'un nom de fichier unique
    ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    input_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, f"{unique_id}{ext}"))
    output_filename = f"{unique_id}.{target_format}"
    output_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, output_filename))

    file.save(input_path)

    try:
        # --- 1. PPTX VERS PDF (via Office) ---
        if ext == '.pptx' and target_format == 'pdf':
            powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
            deck = powerpoint.Presentations.Open(input_path, WithWindow=False)
            deck.SaveAs(output_path, 32) # 32 = format PDF
            deck.Close()
            powerpoint.Quit()

        # --- 2. PDF VERS PPTX (via Aspose) ---
        elif ext == '.pdf' and target_format == 'pptx':
            doc = ap.Document(input_path)
            save_options = ap.PptxSaveOptions()
            doc.save(output_path, save_options)
        
        # --- 3. PDF VERS DOCX (via pdf2docx) ---
        elif ext == '.pdf' and target_format == 'docx':
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
        
        # --- 4. DOCX VERS PDF (via docx2pdf) ---
        elif ext == '.docx' and target_format == 'pdf':
            d2p(input_path, output_path)

        # --- 5. IMAGES VERS PDF (via img2pdf) ---
        elif ext in ['.jpg', '.png', '.jpeg'] and target_format == 'pdf':
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(input_path))
                
# --- 6. HTML VERS PDF (xhtml2pdf - Compatible Windows/Linux) ---
        elif ext == '.html' and target_format == 'pdf':
            with open(output_path, "wb") as result_file:
                with open(input_path, "rb") as source_file:
                    pisa_status = pisa.CreatePDF(source_file, dest=result_file)
            
            if pisa_status.err:
                return jsonify({"error": "Erreur lors de la génération du PDF HTML"}), 500
        else:
            return jsonify({"error": "Combinaison de formats non supportée"}), 400

        return jsonify({"success": True, "download_url": f"/download/{output_filename}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    # Récupère le port du serveur, sinon utilise 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    # '0.0.0.0' permet au serveur d'être accessible depuis l'extérieur
    app.run(host='0.0.0.0', port=port)