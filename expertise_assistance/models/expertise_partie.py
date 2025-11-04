# -*- coding: utf-8 -*-

from odoo import fields, models, api
import json


class ExpertisePartie(models.Model):
    _name = "expertise.partie"
    _description = "Partie au dossier"
    _order = "role, nom_prenom"

    dossier_id = fields.Many2one(
        'expertise.assistance',
        string="Dossier",
        required=True,
        ondelete='cascade',
        index=True
    )

    id_partie = fields.Integer(
        string="ID Partie",
        help="Identifiant unique de la partie dans l'API"
    )

    nom_prenom = fields.Char(
        string="Nom et Prénom",
        help="Nom et prénom de la partie (nomPrenomPartie)"
    )

    role = fields.Char(
        string="Rôle",
        help="Rôle de la partie: مدعي (Demandeur), مدعى عليه (Défendeur)"
    )

    type_personne = fields.Selection([
        ('PP', 'Personne Physique'),
        ('PM', 'Personne Morale')
    ], string="Type de Personne", help="PP = Personne Physique, PM = Personne Morale")

    count_avocats = fields.Integer(
        string="Avocats",
        default=0,
        help="Nombre d'avocats de la partie"
    )

    count_mandataires = fields.Integer(
        string="Mandataires",
        default=0,
        help="Nombre de mandataires de la partie"
    )

    count_huissiers = fields.Integer(
        string="Huissiers",
        default=0,
        help="Nombre d'huissiers de la partie"
    )

    count_representants = fields.Integer(
        string="Représentants",
        default=0,
        help="Nombre de représentants de la partie"
    )

    # Nouveau champ pour stocker TOUTES les données JSON
    raw_data = fields.Json(
        string="Données JSON Complètes",
        help="Toutes les données de la partie au format JSON"
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
                    lines.append("║         TOUTES LES DONNÉES DE LA PARTIE                    ║")
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
