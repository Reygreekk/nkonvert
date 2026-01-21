import os
import uuid
import shutil
import random
import time
import base64
import tempfile
import yt_dlp
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
    
@app.route('/tooltube')
def youtube_page():
    return render_template('tooltube.html')
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


# --- LOGIQUE 2 : NYOUTUBE (NOUVEAU) ---
@app.route('/extract_yt', methods=['POST'])
def extract_yt():
    cleanup_old_files()
    url = request.form.get('url')
    if not url: return jsonify({"success": False, "error": "Lien vide"}), 400

    ydl_opts = {
        'format': 'best', # Récupère le meilleur combo audio/vidéo
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'youtube_include_dash_manifest': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # --- LOGIQUE DE RÉCUPÉRATION DU LIEN ---
            video_url = None
            
            # Cas 1 : Lien direct dans info (YouTube / Twitter)
            video_url = info.get('url')
            
            # Cas 2 : Lien caché dans les formats (Facebook / Instagram)
            if not video_url and 'formats' in info:
                # On cherche un format qui a à la fois la vidéo ET l'audio (pour éviter le muet)
                best_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                if best_formats:
                    video_url = best_formats[-1]['url']

            # Cas 3 : Cas des Reels/Entries
            if not video_url and 'entries' in info:
                video_url = info['entries'][0].get('url')

            if not video_url:
                return jsonify({"success": False, "error": "Impossible d'extraire le lien direct."})

            return jsonify({
                "success": True,
                "title": info.get('title', 'Médias TOOLTUBE'),
                "thumbnail": info.get('thumbnail', ''),
                "video_url": video_url,
                "audio_url": video_url
            })
            
    except Exception as e:
        print(f"Erreur TOOLTUBE : {str(e)}")
        return jsonify({"success": False, "error": "Lien privé, protégé ou invalide."})


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
             "Je suis là pour toi si besoin ! Voici une parole pour te faire sourire :",
            "Voici encore une parole pour toi et te faire du bien :"
        ])
    else:
        intro = random.choice([
            "On a toujours besoin d'une personne qui nous dit ce qu'il faut:",
            "On dirait que tu cherches le bon conseil...",
            f"Je wanda seulement sur toi {prenom or 'ami'}...",
            "j'apprecie beaucoup ta compagnie et cette discussion ;  Voici une autre parole :"
        ])

    branches = {
        "Confiance & Puissance": {
        "sujets": ["Ta valeur", "Ta lumière", "Ta force intérieure", "Ta destinée", "Ton intuition", "Ta détermination", "Ta confiance", "Ta vision", "Ta réussite", "Ta persévérance", "Ta passion"],
    
        "actions": ["est une énergie qui va", "te donne le pouvoir de", "est faite pour", "finit toujours par", "commence enfin à", "te pousse chaque jour à","agit en silence pour", "ne demande qu'à", "est la clé pour", "te permet réellement de"],
        
        "finalites": ["réaliser l'impossible.", "transformer tes rêves en réalité.", "briser tes propres limites.", "attirer l'abondance.", "changer ton monde.", "illuminer ton entourage.","bâtir un empire durable.", "écraser tes doutes.", "devenir inarrêtable.", "laisser une trace indélébile."]
    
    },
        "Confiance en tes capacités": {
            "sujets": ["Tu es la réponse"],
            "actions": ["de Dieu"],
            "finalites": ["aux prieres de quelqu'un."]
        },
          "Confiance à ton aura": {
            "sujets": ["A la Base "],
            "actions": ["nous sommes"],
            "finalites": ["là pour le Buzz."]
        },
         "Confiance en ta personne": {
            "sujets": ["Ta vie compte"],
            "actions": ["pour quelqu'un"],
            "finalites": ["ne l'oublie pas."]
        },
          "Patiente": {
            "sujets": ["Sans expérience l'enthousiasme"],
            "actions": ["n'est pas bon,"],
            "finalites": ["à trop se hater on commet des erreurs."]
        },
          "la critique": {
            "sujets": ["Celui qui accepte"],
            "actions": ["les reproches aime s'instruire"],
            "finalites": [";il est stupide de détester les critiques."]
        },
          "Proverbes du sage": {
            "sujets": ["Il y'a des amis qui menent"],
            "actions": ["au malheur,"],
            "finalites": ["Un ami véritable est plus loyal qu'un frere."]
        },
        "Confiance": {
            "sujets": ["Pour Dieu"],
            "actions": ["tu as plus de valeur"],
            "finalites": ["que le plus beau diamant du monde alors ne laisse personne te dévaloriser."]
        },
        "positivité": {
            "sujets": ["Un esprit positif"],
            "actions": ["engendre une vie qui"],
            "finalites": ["est productive.", "réalise l'impossible."]
        },
        "Leadership": {
            "sujets": ["Un vrai leader"],
            "actions": ["se construit par"],
            "finalites": ["l'exemplarité."]
        },
        "La sagesse guide tes pas": {
    "sujets": ["La sagesse"],
    "actions": ["éclaire"],
    "finalites": ["le chemin de celui qui l’écoute."]
  },
  "La patience élève l’homme": {
    "sujets": ["Celui qui sait attendre"],
    "actions": ["construit"],
    "finalites": ["un avenir solide."]
  },
  "La parole juste a du poids": {
    "sujets": ["Une parole douce"],
    "actions": ["apaise"],
    "finalites": ["les cœurs les plus troublés."]
  },
  "La discipline précède l’honneur": {
    "sujets": ["La rigueur"],
    "actions": ["ouvre"],
    "finalites": ["les portes de la réussite."]
  },
  "Le cœur droit est une force": {
    "sujets": ["L’homme intègre"],
    "actions": ["marche"],
    "finalites": ["sans crainte ni détour."]
  },
  "La crainte de Dieu élève": {
    "sujets": ["La crainte de l’Éternel"],
    "actions": ["engendre"],
    "finalites": ["la sagesse et la paix."]
  },
  "Le travail fidèle porte du fruit": {
    "sujets": ["La main diligente"],
    "actions": ["produit"],
    "finalites": ["l’abondance en son temps."]
  },
  "La sagesse vaut plus que l’or": {
    "sujets": ["La sagesse"],
    "actions": ["surpasse"],
    "finalites": ["toutes les richesses visibles."]
  },
         "C'est toi": {
            "sujets": ["Ton autorité"],
            "actions": ["se façonne quand tu"],
            "finalites": ["admets et apprends tes échecs."]
        },
        "C'est le moment d'écrire ton histoire": {
            "sujets": ["L'Avenir appartient"],
            "actions": ["à ceux qui croient"],
            "finalites": ["en la valeur de leurs rêves."]
        },
        "Espoir & Résilience": {
            "sujets": ["Ta douleur actuelle", "Ce sentiment d'abandon", "Ton cœur épuisé", "Cette tempête intérieure", "L'obscurité qui t'entoure", "Ton âme blessée", "Ce poids sur tes épaules", "Ta lassitude profonde", "Le silence de tes nuits", "Chaque larme versée", "Ton combat invisible", "Cette sensation de vide", "Ton désir de paix", "La fatigue de ton esprit", "Ce passage difficile", "Ta vulnérabilité", "Cette épreuve immense"],
            "actions": ["n'est pas ta destination finale car elle", "est le terreau fertile qui", "te prépare doucement à", "cache une force insoupçonnée pour", "finit inévitablement par ouvrir sur", "contient les graines de", "travaille en silence pour", "n'est qu'un chapitre qui précède", "te forge une résilience pour", "est le signe précurseur de", "finira par s'effacer devant", "t'invite à découvrir enfin", "se transformera bientôt en"],
            "finalites": ["une aube plus radieuse que jamais.", "une guérison profonde et durable.", "la rencontre avec ta force véritable.", "un renouveau que tu mérites vraiment.", "une paix intérieure inébranlable.", "la plus belle version de ta vie.", "une lumière que rien ne pourra ternir.", "un avenir où tu seras enfin fier.", "la joie de t'être choisi(e) à nouveau."]
        },
        "Profondeur": {
            "sujets": ["Notre Foi"],
            "actions": ["vient de ce que "],
            "finalites": ["l'on entend."]
        },
        "Le moment 'Wanda'": {
            "sujets": ["Même dans le chaos,", "Avant d'agir,"],
            "actions": ["prends toujours"],
            "finalites": ["une minute pour wanda.", "un temps de recul."]
        },
        "Leadership & Impact": {
            "sujets": ["Le leadership d'exception", "L'impact véritable", "Le succès durable", "L'autorité naturelle", "La force de l'exemple", "Le prestige professionnel", "La suprématie mentale", "L'excellence opérationnelle", "La maîtrise de soi", "Le charisme pur", "Le sommet du succès"],
            "actions": ["ne se révèle que chez", "finit par choisir", "est le reflet de l'âme de", "se construit à travers", "est la signature de", "s'ancre profondément dans", "couronne uniquement", "fleurit entre les mains de", "ne sourit qu'à", "définit l'identité de"],
            "finalites": ["ceux qui agissent avec une intégrité absolue.", "ceux qui savent écouter avant de commander.", "ceux qui transforment les obstacles en opportunités.", "ceux qui placent le bien commun avant leur propre ego.", "ceux qui osent décider quand tout le monde hésite.", "ceux qui inspirent par leurs actes.", "ceux qui apprennent une leçon de chaque défaite.", "ceux qui maintiennent une discipline de fer."]
        },
        "Une motivation pour ta vie": {
            "sujets": ["Le doute", "la Peur de se lancer"],
            "actions": ["détruit plus de rêves"],
            "finalites": ["que l'échec ne le fera jamais."]
        },
        "Audace & Discipline": {
            "sujets": ["L'audace", "Avoir de l'audace", "La discipline", "La persévérance", "La victoire"],
            "actions": ["caractérise ceux qui", "devient une réalité pour ceux qui", "finit par couronner ceux qui", "récompense ceux qui"],
            "finalites": ["n'abandonnent jamais.", "osent sortir de leur zone de confort.","travaillent avec passion.","placent la discipline au-dessus de la motivation." ]
        },
        "réussite": {
            "sujets": ["Le succès", "La réussite", "Le leadership", "L'excellence", "L'impact", "La grandeur"],
            "actions": ["se construit par ceux qui", "sourit à ceux qui", "récompense ceux qui", "est la marque de ceux qui"],
            "finalites": ["refusent de se contenter de la médiocrité.","construisent chaque jour une meilleure version d'eux-mêmes.", "placent la discipline au-dessus de la motivation.","marchent dans le respect du travail bien fait."]
        },
        "Ton histoire s'écrit aujourd'hui": {
            "sujets": ["L'héritage d'une vie", "La gloire éternelle", "Une trace indélébile", "L'entrée dans la légende", "La véritable grandeur", "Une influence mondiale", "La destinée héroïque", "Une trace générationnelle", "La couronne du succès", "La mémoire collective", "La marche du progrès", "Une victoire historique", "L'ascension finale", "Le prestige éternel", "Le triomphe de l'âme"],
            "actions": ["ne s'offre désormais qu'à", "se forge uniquement par", "est le trophée réservé à", "est la juste récompense de", "s'écrit par la main de", "appartient exclusivement à", "ne reconnaît aujourd'hui que", "attend patiemment l'arrivée de", "devient le privilège de", "se laisse dompter par", "ne couronne finalement que", "est gravée par l'audace de", "s'aligne sur le destin de", "se mérite par la force de", "est le sanctuaire de"],
            "finalites": ["ceux qui refusent de suivre le troupeau.", "ceux qui osent défier les lois de l'impossible.", "ceux qui bâtissent dans le silence et le sacrifice.", "ceux qui transforment leurs blessures en armes.", "ceux qui marchent quand tous les autres s'arrêtent.", "ceux qui gardent la vision malgré la tempête.", "ceux qui placent l'honneur au-dessus de la facilité.", "ceux qui décident de briser les chaînes du passé.", "ceux qui cultivent une discipline de fer au quotidien.", "ceux qui voient la lumière là où d'autres voient le vide."]
        },
        "Spirituel & Vision": {
            "sujets": ["La Foi", "Le miracle", "La vision", "Le destin", "L'authenticité", "La transformation véritable"],
            "actions": ["choisit son camp chez ceux qui", "s'aligne avec ceux qui", "fleurit entre les mains de ceux qui"],
            "finalites": ["écoutent leur intuition malgré le bruit du monde.", "voient des opportunités partout.", "marchent avec la certitude de la victoire."]
        },
        "Comique": {
            "sujets": ["Sache que si tu dors,", "Si tu attends demain,"],
            "actions": ["ta vie", "ton succès"],
            "finalites": ["dort aussi, réveille-toi !", "Dort ohhh, je t'ai prévenu.", "va t'appeler pour te dire au revoir."]
        },
        "Satire & Réalité": {
            "sujets": ["Ne sois pas"],
            "actions": ["le Tonton ou la tata radine", "l'édoughe"],
            "finalites": ["de ta famille.", "du quartier."]
        }
    }

    if compteur > 19:
        selected_branch = "Comique" if random.random() < 0.3 else random.choice(list(branches.keys()))
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



























