# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import http
from odoo.http import request
import json
import base64
import logging

_logger = logging.getLogger(__name__)


class HelloApiController(http.Controller):
    """
    API simple avec une seule endpoint hello
    """

    @http.route('/api/hello', type='http', auth='user', methods=['GET'], csrf=False, cors='*')
    def hello(self, **kwargs):
        """
        Endpoint hello simple avec authentification utilisateur Odoo
        Nécessite une session utilisateur valide
        """
        try:
            # Récupérer les informations de l'utilisateur connecté
            user = request.env.user
            
            return request.make_json_response({
                'success': True,
                'message': f'Hello {user.name}!',
                'data': {
                    'user_id': user.id,
                    'user_name': user.name,
                    'user_login': user.login,
                    'user_email': user.email or 'Pas d\'email',
                    'company': user.company_id.name if user.company_id else 'Pas de société',
                    'database': request.env.cr.dbname,
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': '/api/hello'
                }
            })
            
        except Exception as e:
            return request.make_json_response({
                'success': False,
                'message': f'Erreur: {str(e)}',
                'endpoint': '/api/hello'
            }, status=500)

    @http.route('/api/dossier/import', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def import_dossiers(self, **kwargs):
        """
        Endpoint pour importer des dossiers depuis n8n
        Accepte un tableau d'objets dossiers
        Auth: none (pas d'authentification requise)
        """
        try:
            # Récupérer les données JSON envoyées
            data = json.loads(request.httprequest.data.decode('utf-8'))
            
            # Si c'est un appel JSON-RPC, extraire les params
            if isinstance(data, dict) and 'params' in data:
                data = data['params']
            
            # Créer un environnement avec SUPERUSER_ID pour les opérations
            env = request.env(user=1)  # user_id 1 = Administrator
            
            if not isinstance(data, list):
                data = [data]  # Si un seul objet, le mettre dans une liste
            
            created_dossiers = []
            errors = []
            
            # Créer une copie des données pour le logging sans les données base64
            data_for_logging = []
            for item in data:
                item_copy = item.copy()
                if item_copy.get('files') and isinstance(item_copy['files'], list):
                    files_summary = []
                    for file_info in item_copy['files']:
                        file_summary = file_info.copy()
                        if 'data' in file_summary:
                            # Remplacer les données base64 par un indicateur
                            file_summary['data'] = f"[BASE64_DATA_{len(file_info.get('data', ''))} chars]"
                        files_summary.append(file_summary)
                    item_copy['files'] = files_summary
                data_for_logging.append(item_copy)
            
            for dossier_data in data:
                try:
                    _logger.info(f"=== Traitement dossier: {dossier_data.get('num_dossier_complet')} ===")
                    _logger.info(f"Nombre de fichiers: {len(dossier_data.get('files', [])) if dossier_data.get('files') else 0}")
                    
                    # Rechercher ou créer le tribunal
                    tribunal = None
                    if dossier_data.get('id_jurisdiction') and dossier_data.get('tribunal'):
                        tribunal = env['tribunal'].search([
                            ('idJuridiction', '=', dossier_data['id_jurisdiction'])
                        ], limit=1)
                        
                        if not tribunal and dossier_data.get('tribunal'):
                            # Rechercher ou créer la ville
                            ville = None
                            if dossier_data.get('ville_tribunal'):
                                ville = env['ville'].search([
                                    ('name', '=', dossier_data['ville_tribunal'])
                                ], limit=1)
                                
                                if not ville:
                                    ville = env['ville'].create({
                                        'name': dossier_data['ville_tribunal']
                                    })
                            
                            # Créer le tribunal
                            tribunal = env['tribunal'].create({
                                'name': dossier_data['tribunal'],
                                'idJuridiction': dossier_data['id_jurisdiction'],
                                'ville_id': ville.id if ville else False,
                                'CA': False
                            })
                    
                    # Préparer les données pour sauvegarde (sans les données base64)
                    data_to_save = dossier_data.copy()
                    
                    # Si des fichiers existent, sauvegarder seulement les métadonnées (pas la data base64)
                    if data_to_save.get('files') and isinstance(data_to_save['files'], list):
                        files_metadata = []
                        for file_info in data_to_save['files']:
                            files_metadata.append({
                                'fileName': file_info.get('fileName'),
                                'fileExtension': file_info.get('fileExtension'),
                                'mimeType': file_info.get('mimeType')
                            })
                        data_to_save['files'] = files_metadata
                    
                    # Créer le dossier expertise.assistance
                    dossier_vals = {
                        'numero_dossier': dossier_data.get('num_dossier'),
                        'numero_dossier_mahakim': dossier_data.get('num_dossier_complet'),
                        'tribunal_id': tribunal.id if tribunal else False,
                        'data': data_to_save  # Stocker les données JSON sans base64
                    }
                    
                    # Vérifier si le dossier existe déjà
                    existing = env['expertise.assistance'].search([
                        ('numero_dossier_mahakim', '=', dossier_data.get('num_dossier_complet'))
                    ], limit=1)
                    
                    if existing:
                        # Mettre à jour
                        existing.write(dossier_vals)
                        created_dossiers.append({
                            'id': existing.id,
                            'reference': existing.reference_dossier,
                            'action': 'updated'
                        })
                    else:
                        # Créer nouveau
                        dossier = env['expertise.assistance'].create(dossier_vals)
                        
                        # Traiter les fichiers si présents et non null
                        if dossier_data.get('files') and isinstance(dossier_data['files'], list):
                            attachments_created = []
                            for file_data in dossier_data['files']:
                                try:
                                    # Vérifier que le fichier a bien des données
                                    if file_data.get('data'):
                                        # Le data est déjà en base64, pas besoin de décoder/ré-encoder
                                        attachment = env['ir.attachment'].create({
                                            'name': file_data.get('fileName', 'document.pdf'),
                                            'datas': file_data.get('data'),  # Base64 string
                                            'res_model': 'expertise.assistance',
                                            'res_id': dossier.id,
                                            'mimetype': file_data.get('mimeType', 'application/pdf'),
                                            'type': 'binary',
                                        })
                                        attachments_created.append(attachment.id)
                                        _logger.info(f"Pièce jointe créée: {attachment.name} (ID: {attachment.id})")
                                except Exception as e:
                                    _logger.error(f"Erreur création pièce jointe: {str(e)}")
                        
                        created_dossiers.append({
                            'id': dossier.id,
                            'reference': dossier.reference_dossier,
                            'action': 'created'
                        })
                
                except Exception as e:
                    errors.append({
                        'dossier': dossier_data.get('num_dossier_complet', 'inconnu'),
                        'error': str(e)
                    })
                    _logger.error(f"Erreur import dossier: {str(e)}")
            
            return request.make_json_response({
                'success': True,
                'message': f'{len(created_dossiers)} dossier(s) traité(s)',
                'data': {
                    'dossiers': created_dossiers,
                    'errors': errors,
                    'total_processed': len(data),
                    'total_success': len(created_dossiers),
                    'total_errors': len(errors),
                    'timestamp': datetime.now().isoformat(),
                    'received_data_summary': data_for_logging  # Données reçues sans base64
                }
            })
            
        except Exception as e:
            _logger.error(f"Erreur endpoint import: {str(e)}")
            return request.make_json_response({
                'success': False,
                'message': f'Erreur: {str(e)}',
                'endpoint': '/api/dossier/import'
            }, status=500)

