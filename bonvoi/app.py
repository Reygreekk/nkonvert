from flask import Flask, render_template, request, send_file, jsonify
from fpdf import FPDF
import random
import os

app = Flask(__name__)

def generer_boost_unique():
    sujets = ["L'avenir", "Le succès", "La réussite", "Le destin", "Le bonheur", "Chaque effort", "La persévérance", "Le courage", "L'audace", "Le génie"]
    actions = ["appartient à ceux qui", "se construit par ceux qui", "est le reflet de ceux qui", "sourit toujours à ceux qui", "ne demande qu'à rencontrer ceux qui", "finit par récompenser ceux qui", "est un cadeau pour ceux qui"]
    finalites = ["croient en leurs rêves.", "n'abandonnent jamais.", "osent sortir de leur zone de confort.", "travaillent avec passion.", "voient des opportunités dans chaque défi.", "agissent malgré la peur.", "cultivent la discipline.", "gardent une vision claire.", "savent transformer l'échec en leçon.", "misent sur leur propre valeur.", "gardent la tête haute.", "apprennent chaque jour quelque chose de nouveau.", "font preuve de patience.", "osent être eux-mêmes.", "repoussent leurs limites."]
    return f"{random.choice(sujets)} {random.choice(actions)} {random.choice(finalites)}"

@app.route('/')
def index():
    return render_template('motivation.html')

@app.route('/generate_ajax', methods=['POST'])
def generate_ajax():
    prenom = request.form.get('prenom', 'Aventurier')
    nom = request.form.get('nom', '')
    
    # 1. Générer la phrase
    phrase = generer_boost_unique()
    
    # 2. On peut quand même préparer le fichier si l'utilisateur veut le télécharger plus tard
    # Mais ici on renvoie surtout la phrase pour l'affichage immédiat
    return jsonify({
        "status": "success",
        "phrase": phrase,
        "username": f"{prenom} {nom}"
    })

if __name__ == '__main__':
    # Récupère le port du serveur, sinon utilise 3500 par défaut
    port = int(os.environ.get("PORT", 3500))
    # '0.0.0.0' permet au serveur d'être accessible depuis l'extérieur
    app.run(host='0.0.0.0', port=port)