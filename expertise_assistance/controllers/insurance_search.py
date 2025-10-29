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
            
            for dossier_data in data:
                try:
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
                    
                    # Créer le dossier expertise.assistance
                    dossier_vals = {
                        'numero_dossier': dossier_data.get('num_dossier'),
                        'numero_dossier_mahakim': dossier_data.get('num_dossier_complet'),
                        'tribunal_id': tribunal.id if tribunal else False,
                        'data': dossier_data  # Stocker toutes les données JSON
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
                        
                        # Traiter les fichiers si présents
                        if dossier_data.get('files'):
                            attachments_created = []
                            for file_data in dossier_data['files']:
                                try:
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
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            _logger.error(f"Erreur endpoint import: {str(e)}")
            return request.make_json_response({
                'success': False,
                'message': f'Erreur: {str(e)}',
                'endpoint': '/api/dossier/import'
            }, status=500)

