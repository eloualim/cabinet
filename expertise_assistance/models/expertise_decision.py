# -*- coding: utf-8 -*-

from odoo import fields, models, api
import json


class ExpertiseDecision(models.Model):
    _name = "expertise.decision"
    _description = "Décision de justice"
    _order = "date_time_decision desc"

    dossier_id = fields.Many2one(
        'expertise.assistance',
        string="Dossier",
        required=True,
        ondelete='cascade',
        index=True
    )

    id_decision = fields.Integer(
        string="ID Décision",
        help="Identifiant unique de la décision dans l'API"
    )

    date_time_decision = fields.Datetime(
        string="Date Décision",
        help="Date et heure de la décision (dateTimeDecision)"
    )

    type_decision = fields.Char(
        string="Type de Décision",
        help="Type de décision (typeDecision)"
    )

    contenu_decision = fields.Text(
        string="Contenu",
        help="Contenu de la décision (contenuDecision)"
    )

    date_time_next_audience = fields.Datetime(
        string="Prochaine Audience",
        help="Date et heure de la prochaine audience (dateTimeNextAudience)"
    )

    numero_jugement = fields.Char(
        string="N° Jugement",
        help="Numéro du jugement (numeroJugement)"
    )

    date_de = fields.Date(
        string="Date DE",
        help="Date DE (dateDe)"
    )

    date_na = fields.Date(
        string="Date NA",
        help="Date NA (dateNA)"
    )

    # Nouveau champ pour stocker TOUTES les données JSON
    raw_data = fields.Json(
        string="Données JSON Complètes",
        help="Toutes les données de la décision au format JSON"
    )

    raw_data_formatted = fields.Text(
        string="Toutes les Données",
        compute='_compute_raw_data_formatted',
        help="Affichage formaté de toutes les données JSON"
    )

    @api.depends('raw_data')
    def _compute_raw_data_formatted(self):
        """Formate les données JSON pour un affichage lisible sous forme de tableau"""
        for record in self:
            if record.raw_data:
                try:
                    lines = []
                    lines.append("╔════════════════════════════════════════════════════════════╗")
                    lines.append("║         TOUTES LES DONNÉES DE LA DÉCISION                  ║")
                    lines.append("╠════════════════════════════════════════════════════════════╣")
                    
                    # Parcourir toutes les clés/valeurs du JSON
                    for key, value in record.raw_data.items():
                        # Formater la valeur
                        if isinstance(value, (dict, list)):
                            value_str = json.dumps(value, ensure_ascii=False, indent=2)
                        else:
                            value_str = str(value) if value is not None else "N/A"
                        
                        # Limiter la longueur pour l'affichage
                        if len(value_str) > 100:
                            value_str = value_str[:97] + "..."
                        
                        lines.append(f"║ {key:30s} : {value_str:25s} ║")
                    
                    lines.append("╚════════════════════════════════════════════════════════════╝")
                    record.raw_data_formatted = "\n".join(lines)
                except Exception as e:
                    record.raw_data_formatted = f"Erreur de formatage: {str(e)}"
            else:
                record.raw_data_formatted = "Aucune donnée disponible"
