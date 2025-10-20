# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import http
from odoo.http import request


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

