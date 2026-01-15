import os
import uuid
import shutil
import random
import time
from datetime import timedelta  
import base64
import tempfile
from io import BytesIO
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image

# --- BIBLIOTHÈQUES LÉGÈRES ---
import img2pdf
import mammoth
import fitz  # C'est PyMuPDF
from docx import Document
from pdf2image import convert_from_path
from xhtml2pdf import pisa
from striprtf.striprtf import rtf_to_text
from fpdf import FPDF

app = Flask(__name__)

# --- CONFIGURATION SESSION (24H) ---
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
# --- LOGIQUE 2 : BOOST SPIRIT (Motivation) ---
@app.route('/generate_ajax', methods=['POST'])
def generate_boost():
    session.permanent = True
    # Récupération prénom et nom (facultatifs)
    prenom = request.form.get('prenom', '').strip()
    nom = request.form.get('nom', '').strip()
    
    # Construction de l'identité
    if not prenom and not nom:
        identite = "Aventurier"
    else:
        identite = f"{prenom} {nom}".strip()
    
    # Gestion du compteur
    if 'counter' not in session:
        session['counter'] = 1
    else:
        session['counter'] += 1
    
    compteur = session['counter']

    # --- LOGIQUE D'INTRODUCTION ---
    if compteur == 1:
        intro = f"Bonjour {identite}... J'espère que ta journée se déroule bien jusque-là. Voici ton message boost :"
    elif 1 < compteur <= 12:
        intros_normales = [
            f"Je vois que tu apprécies l'énergie, {prenom or 'ami'}.",
            "On ne s'arrête plus ! Voici encore pour toi :",
            "Voici  encore une parole pour toi et te faire du bien :"
        ]
        intro = random.choice(intros_normales)
    else:
        # APRES 7 CLICS : L'Oracle devient drôle / piquant
        intros_droles = [
            "Dis donc, tu as pris un abonnement ?",
            "On dirait que tu cherches le bon conseil, je vais essayer de te donner du sourire...",
            f"Je wanda seulement sur toi {prenom or 'ami'} , voici ta parole de motivation..",
            "Tu n'as pas un travail qui t'attend ? Voici ta dose :"
        ]
        intro = random.choice(intros_droles)

    # --- BRANCHES THÉMATIQUES ---
    branches = {
        "Confiance & Puissance": {
        # 11 Sujets (Féminin Singulier)
        "sujets": [
            "Ta valeur", "Ta lumière", "Ta force intérieure", "Ta destinée", "Ton intuition", 
            "Ta détermination", "Ta confiance", "Ta vision", "Ta réussite", "Ta persévérance", "Ta passion"
        ],
        # 10 Actions (Liaison vers Infinitif)
        "actions": [
            "est une énergie qui va", "te donne le pouvoir de", "est faite pour", 
            "finit toujours par", "commence enfin à", "te pousse chaque jour à", 
            "agit en silence pour", "ne demande qu'à", "est la clé pour", "te permet réellement de"
        ],
        # 10 Finalités (Verbes à l'infinitif)
        "finalites": [
            "réaliser l'impossible.", "transformer tes rêves en réalité.", "briser tes propres limites.", 
            "attirer l'abondance.", "changer ton monde.", "illuminer ton entourage.", 
            "bâtir un empire durable.", "écraser tes doutes.", "devenir inarrêtable.", "laisser une trace indélébile."
        ]
        # TOTAL : 11 x 10 x 10 = 1 100 combinaisons parfaites
    },
        "Confiance en soi": {
            "sujets": ["le succes ", "Ton potentiel", "Ta lumière"],
            "actions": ["est un état d'esprit"],
            "finalites": ["pour réussir commence à penser comme un Gagnant.", "qui te permet de réaliser l'impossible."]
        },
        "Confiance en tes capacités": {
            "sujets": ["Vous etes la réponse"],
            "actions": ["de Dieu aux prieres"],
            "finalites": ["Aux prieres d'une personne."]
        },
        "positivité": {
            "sujets": ["Un esprit positif"],
            "actions": ["engendre une vie qui", "est un feu qui"],
            "finalites": ["est productive.", "réalise l'impossible."]
        },
        "Leadership": {
            "sujets": ["Un vrai leader", "Ton autorité"],
            "actions": ["se construit par", "naît quand tu"],
            "finalites": ["l'exemplarité.", "acceptes tes échecs."]
        },
        "C'est le moment d'écrire l'histoire": {
            "sujets": ["L'Avenir appartient"],
            "actions": ["à ceux qui croient"],
            "finalites": ["en la valeur de leurs rêves."]
        },
        "Espoir & Résilience": {
    # 20 Sujets : Valider la douleur tout en ouvrant une porte
    "sujets": [
        "Ta douleur actuelle", "Ce sentiment d'abandon", "Ton cœur épuisé", 
        "Cette tempête intérieure", "L'obscurité qui t'entoure", "Ton âme blessée", 
        "Ce poids sur tes épaules", "Ta lassitude profonde", "Le silence de tes nuits", 
        "Chaque larme versée", "Ton combat invisible", "Cette sensation de vide", 
        "Ton désir de paix", "La fatigue de ton esprit", "Ton histoire inachevée", 
        "Ce passage difficile", "Ton besoin de lumière", "Ta vulnérabilité", 
        "Ton sentiment d'impasse", "Cette épreuve immense"
    ],
    
    # 16 Liaisons : Le pont vers la transformation
    "actions": [
        "n'est pas ta destination finale car elle", "est le terreau fertile qui", 
        "te prépare doucement à", "cache une force insoupçonnée pour", 
        "finit inévitablement par ouvrir sur", "contient les graines de", 
        "travaille en silence pour", "n'est qu'un chapitre qui précède", 
        "te forge une résilience pour", "est le signe précurseur de", 
        "finira par s'effacer devant", "t'invite à découvrir enfin", 
        "ne pourra jamais éteindre", "est la preuve que tu possèdes", 
        "se transformera bientôt en", "s'aligne aujourd'hui pour protéger"
    ],
    
    # 10 Finalités : La lumière au bout du tunnel
    "finalites": [
        "une aube plus radieuse que jamais.", 
        "une guérison profonde et durable.", 
        "la rencontre avec ta force véritable.", 
        "un renouveau que tu mérites vraiment.", 
        "une paix intérieure inébranlable.", 
        "la plus belle version de ta vie.", 
        "une lumière que rien ne pourra ternir.", 
        "un avenir où tu seras enfin fier.", 
        "la joie de t'être choisi(e) à nouveau.", 
        "une raison d'être plus grande que ta peine."
    ]
},
        
        "Audace & Discipline": {
            "sujets": ["L'audace", "Avoir de l'audace", "La discipline", "La persévérance", "La victoire"],
            "actions": ["caractérise ceux qui", "devient une réalité pour ceux qui", "finit par couronner ceux qui", "récompense ceux qui"],
            "finalites": [
                "n'abandonnent jamais.", 
                "osent sortir de leur zone de confort.", 
                "travaillent avec passion.",
                "placent la discipline au-dessus de la motivation."
            ]
        },
        "Le moment 'Wanda'": {
            "sujets": ["Même dans le chaos,", "Avant d'agir,"],
            "actions": ["prends toujours"],
            "finalites": ["une minute pour wanda.", "un temps de recul."]
        },
        "Ton histoire s'écrit aujourd'hui": {
    # 15 Sujets (La cible)
    "sujets": [
        "L'héritage d'une vie", "La gloire éternelle", "Une trace indélébile", 
        "L'entrée dans la légende", "La véritable grandeur",  "Une influence mondiale", "La destinée héroïque", "Une trace générationnelle", "La couronne du succès", "La mémoire collective", 
        "La marche du progrès", "Une victoire historique" ],
    
    # 15 Liaisons (Le moteur vers "ceux qui")
    "actions": [
        "ne s'offre désormais qu'à", "se forge uniquement par", "est le trophée réservé à", 
        "est la juste récompense de", "s'écrit par la main de", "appartient exclusivement à", 
        "ne reconnaît aujourd'hui que", "attend patiemment l'arrivée de", "devient le privilège de", 
        "se laisse dompter par", "ne couronne finalement que", "est gravée par l'audace de", 
        "s'aligne sur le destin de", "se mérite par la force de", "est le sanctuaire de"
    ],
    
    # 10 Profils (L'identité "ceux qui" + l'action)
    "finalites": [
        "ceux qui refusent de suivre le troupeau.", 
        "ceux qui osent défier les lois de l'impossible.", 
        "ceux qui bâtissent dans le silence et le sacrifice.", 
        "ceux qui transforment leurs blessures en armes.", 
        "ceux qui marchent quand tous les autres s'arrêtent.", 
        "ceux qui gardent la vision malgré la tempête.", 
        "ceux qui placent l'honneur au-dessus de la facilité.", 
        "ceux qui décident de briser les chaînes du passé.", 
        "ceux qui cultivent une discipline de fer au quotidien.", 
        "ceux qui voient la lumière là où d'autres voient le vide."
    ]
},
        
        "Spirituel & Vision": {
            "sujets": ["La Foi", "Le miracle", "La vision", "Le destin", "L'authenticité", "La transformation véritable"],
            "actions": ["choisit son camp chez ceux qui", "s'aligne avec ceux qui", "fleurit entre les mains de ceux qui"],
            "finalites": [
                "écoutent leur intuition malgré le bruit du monde.", 
                "voient des opportunités partout.", 
                "marchent avec la certitude de la victoire." # Ajout cohérent
            ]
        },
        "Leadership & Impact": {
    # 15 Sujets : Vocabulaire de haute stature
    "sujets": [
        "Le leadership d'exception", "L'impact véritable", "Le succès durable", 
        "L'autorité naturelle", "La force de l'exemple", "Une ascension fulgurante", 
        "Le prestige professionnel", "L'influence positive", "La suprématie mentale", 
        "Un parcours exemplaire", "L'excellence opérationnelle", "La maîtrise de soi", 
        "Le charisme pur", "La marque des grands", "Le sommet du succès"
    ],
    
    # 14 Liaisons : Pour une connexion fluide avec "ceux qui"
    "actions": [
        "ne se révèle que chez", "finit par choisir", "est le reflet de l'âme de", 
        "se construit à travers", "est la signature de", "s'ancre profondément dans", 
        "devient le bouclier de", "couronne uniquement", "fleurit entre les mains de", 
        "exige la rigueur de", "ne sourit qu'à", "reste le privilège de", 
        "définit l'identité de", "valorise avant tout"
    ],
    
    # 10 Finalités : Profils de leaders inspirants
    "finalites": [
        "ceux qui agissent avec une intégrité absolue.", 
        "ceux qui savent écouter avant de commander.", 
        "ceux qui transforment les obstacles en opportunités.", 
        "ceux qui placent le bien commun avant leur propre ego.", 
        "ceux qui osent décider quand tout le monde hésite.", 
        "ceux qui inspirent par leurs actes plutôt que par leurs mots.", 
        "ceux qui apprennent une leçon de chaque défaite.", 
        "ceux qui maintiennent une discipline de fer dans le chaos.", 
        "ceux qui croient en leur vision malgré les critiques.", 
        "ceux qui cultivent l'excellence dans les plus petits détails."
    ]
},
        "Profondeur": {
            "sujets": ["Notre Foi"],
            "actions": ["vient de ce que "],
            "finalites": ["l'on entend."]
        },
        
        "réussite": {
            "sujets": ["Le succès", "La réussite", "Le leadership", "L'excellence", "L'impact", "La grandeur"],
            "actions": ["se construit par ceux qui", "sourit à ceux qui", "récompense ceux qui", "est la marque de ceux qui"],
            "finalites": [
                "refusent de se contenter de la médiocrité.", 
                "construisent chaque jour une meilleure version d'eux-mêmes.", 
                "placent la discipline au-dessus de la motivation.",
                "marchent dans le respect du travail bien fait."
            ]
        },
        
        "Une motivation pour ta vie": {
            "sujets": ["Le doute", "la Peur de se lancer"],
            "actions": ["détruit plus de rêves"],
            "finalites": ["que l'échec ne le fera jamais."]
        },
        "Satire & Réalité": { # Branche drôle
            "sujets": [ "Ne sois pas"],
            "actions": ["le Tonton ou la tata radine", "l'édoughe"],
            "finalites": ["de ta famille."]
        },
        "Comique": { # Branche drôle
            "sujets": ["Sache que si tu dors,"],
            "actions": ["ta vie"],
            "finalites": ["dort aussi, réveille-toi !","Dort ohhh, je t'ai prévenu."]
        }
    }

    # --- SÉLECTION DE LA CATÉGORIE ---
    # Si compteur > 7, on force 70% de chance sur la Satire
    if compteur > 18:
        if random.random() < 0.3:
            selected_branch = "Comique"
        else:
            selected_branch = random.choice(list(branches.keys()))
    else:
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









