# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
import requests
import json

_logger = logging.getLogger(__name__)


class ExpertiseAssistance(models.Model):
    _name = "expertise.assistance"
    _description = "Expertise Assistance"
    _order = "reference_dossier desc"
    _rec_name = "reference_dossier"

    reference_dossier = fields.Char(
        string="Référence Dossier",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('expertise.assistance') or '/',
        help="Référence unique du dossier générée automatiquement"
    )

    numero_dossier = fields.Char(
        string="Numéro de Dossier",
        help="Numéro du dossier"
    )

    numero_dossier_mahakim = fields.Char(
        string="Numéro Dossier Mahakim",
        help="Numéro du dossier dans le système Mahakim"
    )

    ca_tribunal_id = fields.Many2one(
        'tribunal',
        string="Tribunal CA",
        ondelete='restrict',
        domain="[('CA', '=', True)]",
        help="Tribunal de la Cour d'Appel"
    )

    tribunal_id = fields.Many2one(
        'tribunal',
        string="Tribunal",
        ondelete='restrict',
        domain="[('parent_id', '=', ca_tribunal_id)]",
        help="Tribunal associé au dossier (filtré par le Tribunal CA)"
    )

    idjuridiction = fields.Char(
        string="ID Juridiction",
        compute='_compute_idjuridiction',
        store=True,
        help="ID Juridiction du tribunal sélectionné (tribunal_id si présent, sinon ca_tribunal_id)"
    )

    data = fields.Json(
        string="Données JSON",
        help="Données au format JSON"
    )

    data_formatted = fields.Text(
        string="Données Formatées",
        compute='_compute_data_formatted',
        help="Affichage formaté des données JSON"
    )

    resume = fields.Text(
        string="Résumé du Dossier",
        compute='_compute_resume',
        help="Résumé des informations principales du dossier"
    )

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'expertise.assistance')],
        string="Pièces Jointes",
        help="Documents attachés au dossier"
    )

    attachment_count = fields.Integer(
        string="Nombre de pièces jointes",
        compute='_compute_attachment_count',
        help="Nombre de fichiers attachés"
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Décocher pour archiver le dossier"
    )

    @api.depends('tribunal_id', 'tribunal_id.idJuridiction', 'ca_tribunal_id', 'ca_tribunal_id.idJuridiction')
    def _compute_idjuridiction(self):
        """Calcule l'ID Juridiction: tribunal_id en priorité, sinon ca_tribunal_id"""
        for record in self:
            if record.tribunal_id and record.tribunal_id.idJuridiction:
                record.idjuridiction = record.tribunal_id.idJuridiction
            elif record.ca_tribunal_id and record.ca_tribunal_id.idJuridiction:
                record.idjuridiction = record.ca_tribunal_id.idJuridiction
            else:
                record.idjuridiction = False

    @api.depends('data')
    def _compute_data_formatted(self):
        """Formate les données JSON pour un affichage lisible"""
        for record in self:
            if record.data:
                try:
                    record.data_formatted = json.dumps(record.data, indent=4, ensure_ascii=False, sort_keys=True)
                except Exception as e:
                    record.data_formatted = f"Erreur de formatage: {str(e)}\n\nDonnées brutes: {record.data}"
            else:
                record.data_formatted = ""

    @api.depends('data')
    def _compute_resume(self):
        """Génère un résumé lisible des informations principales du dossier"""
        for record in self:
            if not record.data:
                record.resume = ""
                continue
            
            try:
                data = record.data.get('data', {}) if isinstance(record.data, dict) else {}
                carte = data.get('carte', {})
                parties = data.get('parties', [])
                expertises = data.get('expertises', [])
                decisions = data.get('decisions', [])
                
                resume_parts = []
                
                # === INFORMATIONS GÉNÉRALES ===
                resume_parts.append("═══════════════════════════════════════════════")
                resume_parts.append("         RÉSUMÉ DU DOSSIER")
                resume_parts.append("═══════════════════════════════════════════════\n")
                
                if carte:
                    resume_parts.append("📋 INFORMATIONS GÉNÉRALES")
                    resume_parts.append("─────────────────────────────────────────────")
                    resume_parts.append(f"Numéro Dossier: {carte.get('numeroCompletDossier1Instance', 'N/A')}")
                    resume_parts.append(f"Numéro National: {carte.get('numeroCompletNationalDossier1Instance', 'N/A')}")
                    resume_parts.append(f"Type d'affaire: {carte.get('affaire', 'N/A')}")
                    resume_parts.append(f"Entité: {carte.get('libEntite', 'N/A')}")
                    resume_parts.append(f"Type de requête: {carte.get('typeRequette', 'N/A')}")
                    resume_parts.append(f"Date d'enregistrement: {carte.get('dateEnregistrementDossierDansRegistre', 'N/A')}")
                    resume_parts.append("")
                
                # === JURIDICTION ===
                if carte.get('juridiction1Instance'):
                    resume_parts.append("⚖️  JURIDICTION")
                    resume_parts.append("─────────────────────────────────────────────")
                    resume_parts.append(f"Tribunal: {carte.get('juridiction1Instance', 'N/A')}")
                    resume_parts.append(f"Juge Rapporteur: {carte.get('jugeRapporteur', 'N/A')}")
                    resume_parts.append("")
                
                # === PARTIES ===
                if parties:
                    resume_parts.append("👥 PARTIES")
                    resume_parts.append("─────────────────────────────────────────────")
                    for i, partie in enumerate(parties, 1):
                        type_personne = "Personne Morale" if partie.get('codeTypePersonne') == 'PM' else "Personne Physique"
                        resume_parts.append(f"{i}. {partie.get('nomPrenomPartie', 'N/A')}")
                        resume_parts.append(f"   Rôle: {partie.get('rolePartie', 'N/A')} - {type_personne}")
                        if partie.get('countAvocatsPartie', 0) > 0:
                            resume_parts.append(f"   Avocats: {partie.get('countAvocatsPartie')}")
                    resume_parts.append("")
                
                # === EXPERTISES ===
                if expertises:
                    resume_parts.append("🔬 EXPERTISES")
                    resume_parts.append("─────────────────────────────────────────────")
                    for i, expertise in enumerate(expertises, 1):
                        resume_parts.append(f"{i}. Mission: {expertise.get('libMission', 'N/A')}")
                        resume_parts.append(f"   N° Dossier MI: {expertise.get('numeroDossierMI', 'N/A')}")
                        resume_parts.append(f"   État: {expertise.get('etatMission', 'N/A')}")
                        experts = expertise.get('experts', [])
                        if experts:
                            resume_parts.append(f"   Expert(s): {', '.join(experts)}")
                        if expertise.get('dateEtatMission'):
                            resume_parts.append(f"   Date: {expertise.get('dateEtatMission')}")
                    resume_parts.append("")
                
                # === DERNIER JUGEMENT ===
                if carte.get('libelleDernierJugement'):
                    resume_parts.append("📜 DERNIER JUGEMENT")
                    resume_parts.append("─────────────────────────────────────────────")
                    resume_parts.append(f"Libellé: {carte.get('libelleDernierJugement', 'N/A')}")
                    resume_parts.append(f"Date: {carte.get('dateDernierJugement', 'N/A')}")
                    if carte.get('etatDernierJugement'):
                        resume_parts.append(f"État: {carte.get('etatDernierJugement')}")
                    resume_parts.append("")
                
                # === DÉCISIONS RÉCENTES ===
                if decisions:
                    resume_parts.append("📌 DERNIÈRES DÉCISIONS (5 plus récentes)")
                    resume_parts.append("─────────────────────────────────────────────")
                    for i, decision in enumerate(decisions[:5], 1):
                        resume_parts.append(f"{i}. {decision.get('typeDecision', 'N/A')}")
                        resume_parts.append(f"   Date: {decision.get('dateTimeDecision', 'N/A')}")
                        if decision.get('contenuDecision'):
                            resume_parts.append(f"   Contenu: {decision.get('contenuDecision')}")
                        if decision.get('dateTimeNextAudience'):
                            resume_parts.append(f"   Prochaine audience: {decision.get('dateTimeNextAudience')}")
                        resume_parts.append("")
                
                # === STATISTIQUES ===
                resume_parts.append("📊 STATISTIQUES")
                resume_parts.append("─────────────────────────────────────────────")
                resume_parts.append(f"Nombre de parties: {len(parties)}")
                resume_parts.append(f"Nombre d'expertises: {len(expertises)}")
                resume_parts.append(f"Nombre de décisions: {len(decisions)}")
                
                # Timestamp
                if data.get('timestamp'):
                    resume_parts.append(f"\n⏰ Données récupérées le: {data.get('timestamp')}")
                    resume_parts.append(f"Source: {record.data.get('source', 'N/A')}")
                
                record.resume = "\n".join(resume_parts)
                
            except Exception as e:
                record.resume = f"Erreur lors de la génération du résumé: {str(e)}"

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Calcule le nombre de pièces jointes"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    def action_view_attachments(self):
        """Ouvre la vue des pièces jointes"""
        self.ensure_one()
        return {
            'name': 'Pièces Jointes',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', 'expertise.assistance'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'expertise.assistance',
                'default_res_id': self.id,
            }
        }

    @api.onchange('ca_tribunal_id')
    def _onchange_ca_tribunal_id(self):
        """Vide le tribunal_id quand le ca_tribunal_id change"""
        if self.ca_tribunal_id:
            # Si le tribunal sélectionné n'a pas le bon parent, on le vide
            if self.tribunal_id and self.tribunal_id.parent_id != self.ca_tribunal_id:
                self.tribunal_id = False

    @api.model
    def create(self, vals):
        """Génère automatiquement la référence du dossier à la création"""
        if vals.get('reference_dossier', '/') == '/':
            vals['reference_dossier'] = self.env['ir.sequence'].next_by_code('expertise.assistance') or '/'
        return super(ExpertiseAssistance, self).create(vals)

    def action_fetch_dossier_data(self):
        """Récupère les données du dossier depuis l'API Cabinet Sabir"""
        self.ensure_one()
        
        # Vérifier que les champs nécessaires sont remplis
        if not self.idjuridiction:
            raise UserError(_("L'ID Juridiction est requis pour récupérer les données."))
        
        if not self.numero_dossier_mahakim:
            raise UserError(_("Le numéro de dossier Mahakim est requis pour récupérer les données."))
        
        # URL de l'API
        base_url = "https://api.cabinetsabir.ma"
        endpoint = f"/dossier/{self.idjuridiction}/{self.numero_dossier_mahakim}"
        url = base_url + endpoint
        
        try:
            _logger.info(f"Récupération des données du dossier depuis: {url}")
            
            # Appel à l'API
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Lève une exception si erreur HTTP
            
            # Récupération des données JSON
            data = response.json()
            
            # Stockage dans le champ data
            self.data = data
            
            _logger.info(f"Données du dossier {self.reference_dossier} récupérées avec succès")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Succès'),
                    'message': _('Les données du dossier ont été récupérées avec succès.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors de la récupération des données: {str(e)}"
            _logger.error(error_msg)
            raise UserError(_(error_msg))
        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            _logger.error(error_msg)
            raise UserError(_(error_msg))
