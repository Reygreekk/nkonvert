from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import uuid
import img2pdf
import aspose.words as aw        # Pour Word vers PDF
import aspose.slides as slides   # Pour PPTX vers PDF
import aspose.pdf as ap         # Pour PDF vers PPTX
from pdf2docx import Converter   # Pour PDF vers Word
from xhtml2pdf import pisa      # Pour HTML vers PDF

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

    ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}{ext}")
    output_filename = f"{unique_id}.{target_format}"
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)

    file.save(input_path)

    try:
        # --- 1. PPTX VERS PDF (Aspose Slides - Compatible Linux) ---
        if ext == '.pptx' and target_format == 'pdf':
            pres = slides.Presentation(input_path)
            pres.save(output_path, slides.export.SaveFormat.PDF)

        # --- 2. PDF VERS PPTX (Aspose PDF) ---
        elif ext == '.pdf' and target_format == 'pptx':
            doc = ap.Document(input_path)
            doc.save(output_path, ap.PptxSaveOptions())
        
        # --- 3. PDF VERS DOCX (pdf2docx) ---
        elif ext == '.pdf' and target_format == 'docx':
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
        
        # --- 4. DOCX VERS PDF (Aspose Words - Remplace docx2pdf) ---
        elif ext == '.docx' and target_format == 'pdf':
            doc = aw.Document(input_path)
            doc.save(output_path)

        # --- 5. IMAGES VERS PDF ---
        elif ext in ['.jpg', '.png', '.jpeg'] and target_format == 'pdf':
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(input_path))
                
        # --- 6. HTML VERS PDF ---
        elif ext == '.html' and target_format == 'pdf':
            with open(output_path, "wb") as result_file:
                with open(input_path, "rb") as source_file:
                    pisa.CreatePDF(source_file, dest=result_file)

        else:
            return jsonify({"error": "Combinaison non supportée sur ce serveur"}), 400

        return jsonify({"success": True, "download_url": f"/download/{output_filename}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

    app.run(host='0.0.0.0', port=port)

