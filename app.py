
"""TP2"""

from operator import ge
import os
from datetime import date
from email.policy import default
from types import NoneType
from webbrowser import get
from flask import Flask, render_template, request, redirect, url_for
from flask_babel import Babel
from babel import dates
from werkzeug.utils import secure_filename
from bd import creer_connexion

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "static/video/"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000  # 16Mo
app.config['UPLOAD_EXTENSIONS'] = [
    '.mp4', '.mov', '.wmv', '.mpg', '.webm', '.mkv', '.swf']


def get_id_nouveau_video():
    """test"""
    with creer_connexion() as connexion:
        with connexion.get_curseur() as curseur:
            curseur.execute(
                'select MAX(id) from videos')
            id_nouv = curseur.fetchone()
    int_id = int(id_nouv['MAX(id)']) + 1
    return int_id


@ app.route("/", methods=["GET", "POST"])
def index():
    """
    Returns:
        videos
    """
    videos = None
    srcs = [list]
    etiquettes = []
    with creer_connexion() as connexion:
        with connexion.get_curseur() as curseur:
            curseur.execute(
                'select id, titre, description, nom_fichier from videos LIMIT 3')
            videos = curseur.fetchall()
    for le_video in videos:
        srcs.append(app.config['UPLOAD_FOLDER'] + le_video['nom_fichier'])
        if (get_etiquettes(le_video['id']) is not None or "" or []):
            etiquettes.append(get_etiquettes(le_video['id']))
    return render_template("index.jinja", videos=videos, srcs=srcs, etiquettes=etiquettes)


@ app.route("/ajouter", methods=["GET", "POST"])
def form_ajout():
    """
    Returns:
        Formulaire d'ajout
    """
    titre = {}
    description = {}
    nom_fichier = {}
    les_etiquettes = get_toggle_etiquettes()
    erreur = False
    if request.method != "POST":

        return render_template(
            "ajouter.jinja",
            titre=titre,
            description=description,
            hyperlien=nom_fichier,
            etiquettes=les_etiquettes
        )
    else:
        titre = request.form.get("titre", default="").strip()
        description = request.form.get(
            "description", default="").strip()
        fichier = request.files['fichier']
        nom_fichier = secure_filename(fichier.filename)
        fichier_ext = os.path.splitext(nom_fichier)[1]
        msg = ""
        etiquettes_choisies = request.form.getlist("etiquette")
        if fichier.seek(0, os.SEEK_END):
            fichier_length = fichier.tell()
            if fichier_length > app.config['MAX_CONTENT_LENGTH']:
                msg = "Le fichier est trop grand!"
                erreur = True
            elif fichier_ext not in app.config['UPLOAD_EXTENSIONS']:
                msg = "Le type de fichier n'est pas supporté!"
                erreur = True
            fichier.seek(0, 0)
        if erreur:
            return bad_request(msg)

        src = app.config['UPLOAD_FOLDER'] + nom_fichier
        fichier.save(src)
        id_video = get_id_nouveau_video()
        with creer_connexion() as connexion:
            with connexion.get_curseur() as curseur:
                curseur.execute(
                    "INSERT INTO `videos`(`titre`, `description`, `nom_fichier`) VALUES(%(le_titre)s, %(la_description)s, %(nom_fichier)s);", {
                        'le_titre': titre,
                        'la_description': description,
                        'nom_fichier': nom_fichier
                    })
        ajouter_v_libelles(id_video, etiquettes_choisies)
    return redirect(
        url_for('video', titre=titre,
                description=description, id_video=id_video, etiquettes_choisies=etiquettes_choisies)
    )


def ajouter_v_libelles(id_video, etiquettes_choisies):
    """Ajouter le lien entre les videos et les etiquettes"""
    for etiquette in etiquettes_choisies:
        with creer_connexion() as connexion:
            with connexion.get_curseur() as curseur:
                curseur.execute(
                    "INSERT INTO `videos_libelles`(`id_video`, `id_etiquette`) VALUES (%(id_video)s, %(id_etiquette)s)", {
                        'id_video': id_video,
                        'id_etiquette': etiquette
                    })


def get_toggle_etiquettes():
    """Get etiquettes"""
    with creer_connexion() as connexion:
        with connexion.get_curseur() as curseur:
            curseur.execute(
                'select id, libelle from etiquettes')
            les_etiquettes = curseur.fetchall()
    return les_etiquettes


@ app.route("/recherche", methods=["GET", "POST"])
def recherche():
    """
    Returns:
        Page correspondant à la recherche
    """
    videos = None
    mot_cle = request.args.get("mot-cle", default="").strip()
    srcs = [list]

    with creer_connexion() as connexion:
        with connexion.get_curseur() as curseur:
            curseur.execute(
                "select * from videos WHERE titre LIKE %(mot_cle)s;", {
                    'mot_cle': mot_cle
                })
            videos = curseur.fetchall()
    for le_video in videos:
        srcs.append(app.config['UPLOAD_FOLDER'] + le_video['nom_fichier'])
    return render_template("recherche.jinja", videos=videos, srcs=srcs)


@ app.route("/videos", methods=["GET", "POST"])
def videos():
    """
    Returns:
        Videos
    """
    les_videos = None
    srcs = [list]
    with creer_connexion() as connexion:

        with connexion.get_curseur() as curseur:
            curseur = connexion.cursor(buffered=True)
            curseur.execute(
                "select id, titre, description, nom_fichier from videos"
            )
        les_videos = curseur.fetchall()
    for le_video in les_videos:
        srcs.append(app.config['UPLOAD_FOLDER'] + le_video[3])

    return render_template(
        "videos.jinja", videos=les_videos, src=srcs
    )


def get_etiquettes(id_video):
    """Aller chercher les étiquettes pour un video"""
    with creer_connexion() as connexion:
        with connexion.get_curseur() as curseur:
            curseur.execute(
                "select id_etiquette from videos_libelles WHERE `id_video` = %(id_video)s;", {
                    'id_video': id_video
                })
            ids = curseur.fetchall()
    id_etiquettes = []
    for ids_courants in ids:
        id_etiquettes.append(ids_courants['id_etiquette'])
    etiquettes = []
    for id_etiquette in id_etiquettes:
        with creer_connexion() as connexion:
            with connexion.get_curseur() as curseur:
                curseur.execute(
                    "select libelle from etiquettes WHERE `id` = %(id_etiquette)s;", {
                        'id_etiquette': id_etiquette
                    })
                etiquettes.append(curseur.fetchone()['libelle'])
    return etiquettes


@ app.route("/video/<int:id_video>", methods=["GET", "POST"])
def video(id_video):
    """
    Returns:
        Video
    """
    with creer_connexion() as connexion:
        with connexion.get_curseur() as curseur:
            curseur.execute(
                "select id, titre, description, nom_fichier from videos WHERE `id` = %(id_video)s;", {
                    'id_video': id_video
                })
            video = curseur.fetchone()
            src = app.config['UPLOAD_FOLDER'] + video['nom_fichier']
    etiquettes = get_etiquettes(id_video)
    return render_template(
        "video.jinja", video=video, src=src, etiquettes=etiquettes, description=video['description']
    )


@ app.route("/etiquettes", methods=["GET", "POST"])
def etiquettes():
    """Page d'étiquettes"""

    etiquettes = get_toggle_etiquettes()

    return render_template(
        "etiquettes.jinja", etiquettes=etiquettes
    )


@ app.errorhandler(400)
def bad_request(_e):
    """bruh"""
    return "Erreur 400 : Bad_request - " + _e


if __name__ == '__main__':
    app.run(debug=True)
