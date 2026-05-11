"""
routes/settings.py
Route Flask pour sauvegarder les préférences UI de l'utilisateur.
"""

from flask import Blueprint, request, jsonify, session
from models.user import User, db
import json
import logging

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/save', methods=['POST'])
def save_settings():
    """Sauvegarde les paramètres UI en base de données."""

    # Vérifier la session
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Non authentifié'}), 401

    # Récupérer les données JSON
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Données manquantes'}), 400

    # Valider les champs autorisés
    allowed_keys = {'theme', 'primaryColor', 'fontFamily', 'fontSize', 'background',
                    'sidebarCompact', 'animations'}
    settings = {k: v for k, v in data.items() if k in allowed_keys}

    # Valider les valeurs
    valid_themes = {'dark-mode', 'light-mode', 'theme-ocean', 'theme-forest',
                    'theme-sunset', 'theme-purple'}
    valid_fonts = {'Segoe UI', 'Georgia', 'Courier New', 'Arial',
                   'Trebuchet MS', 'Palatino'}
    valid_bgs = {'bg-none', 'bg-grad-1', 'bg-grad-2', 'bg-grad-3',
                 'bg-grad-4', 'bg-grad-5', 'bg-grad-6', 'bg-grad-7', 'bg-grad-8'}

    if 'theme' in settings and settings['theme'] not in valid_themes:
        return jsonify({'success': False, 'error': 'Thème invalide'}), 400
    if 'fontFamily' in settings and settings['fontFamily'] not in valid_fonts:
        return jsonify({'success': False, 'error': 'Police invalide'}), 400
    if 'background' in settings and settings['background'] not in valid_bgs:
        return jsonify({'success': False, 'error': 'Fond invalide'}), 400
    if 'fontSize' in settings:
        try:
            fs = int(settings['fontSize'])
            if not (12 <= fs <= 20):
                raise ValueError
            settings['fontSize'] = fs
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Taille de police invalide'}), 400

    # Chercher l'utilisateur
    username = session['user']
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'error': 'Utilisateur introuvable'}), 404

    # Sauvegarder
    try:
        user.ui_settings = json.dumps(settings)
        db.session.commit()
        logger.info(f"[SETTINGS] Paramètres sauvegardés pour {username}: {settings}")
        return jsonify({'success': True, 'message': 'Paramètres sauvegardés'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"[SETTINGS] Erreur: {e}")
        return jsonify({'success': False, 'error': 'Erreur base de données'}), 500


@settings_bp.route('/get', methods=['GET'])
def get_settings():
    """Retourne les paramètres UI de l'utilisateur."""
    if 'user' not in session:
        return jsonify({'success': False}), 401

    user = User.query.filter_by(username=session['user']).first()
    if not user:
        return jsonify({'success': False}), 404

    try:
        settings = json.loads(user.ui_settings) if user.ui_settings else {}
        return jsonify({'success': True, 'settings': settings})
    except Exception:
        return jsonify({'success': True, 'settings': {}})
