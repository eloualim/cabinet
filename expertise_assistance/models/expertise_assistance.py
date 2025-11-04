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
    _inherit = ['mail.thread', 'mail.activity.mixin']

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

    # Nouveaux champs
    status = fields.Selection([
        ('incorrect', 'Incorrect'),
        ('incomplete', 'Incomplet'),
        ('complete', 'Complet')
    ], string="Statut", default='incomplete', required=True, tracking=True,
       help="Statut de complétude du dossier")

    magistrat = fields.Char(
        string="Magistrat",
        tracking=True,
        help="Nom du magistrat/juge rapporteur"
    )

    greffier = fields.Char(
        string="Greffier",
        tracking=True,
        help="Nom du greffier"
    )

    date_prochaine_audience = fields.Datetime(
        string="Prochaine Audience",
        tracking=True,
        help="Date et heure de la prochaine audience"
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

    parties_ids = fields.One2many(
        'expertise.partie',
        'dossier_id',
        string="Parties",
        help="Liste des parties au dossier"
    )

    decisions_ids = fields.One2many(
        'expertise.decision',
        'dossier_id',
        string="Décisions",
        help="Liste des décisions"
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
        """Génère un résumé lisible des informations principales du dossier - Version flexible"""
        for record in self:
            if not record.data:
                record.resume = ""
                continue
            
            try:
                data = record.data.get('data', {}) if isinstance(record.data, dict) else {}
                carte = data.get('carte', {})
                parties = data.get('parties', [])
                expertises = data.get('expertises', {})
                decisions = data.get('decisions', [])
                
                resume_parts = []
                
                # === INFORMATIONS GÉNÉRALES ===
                resume_parts.append("═══════════════════════════════════════════════")
                resume_parts.append("         RÉSUMÉ DU DOSSIER")
                resume_parts.append("═══════════════════════════════════════════════\n")
                
                if carte:
                    resume_parts.append("📋 INFORMATIONS GÉNÉRALES")
                    resume_parts.append("─────────────────────────────────────────────")
                    
                    # Numéro dossier - flexible
                    numero = carte.get('numeroDossierComplet') or carte.get('numeroCompletDossier1Instance') or 'N/A'
                    resume_parts.append(f"Numéro Dossier: {numero}")
                    
                    # Nature affaire
                    nature = carte.get('natureAffaire') or carte.get('affaire') or 'N/A'
                    resume_parts.append(f"Nature d'affaire: {nature}")
                    
                    # Entité
                    entite = carte.get('entite') or carte.get('libEntite') or 'N/A'
                    resume_parts.append(f"Entité: {entite}")
                    
                    # Date enregistrement
                    date_enreg = carte.get('dateEnregistrementString') or carte.get('dateEnregistrementDossierDansRegistre') or 'N/A'
                    resume_parts.append(f"Date d'enregistrement: {date_enreg}")
                    resume_parts.append("")
                
                # === DERNIER JUGEMENT (depuis carte.lastJugement) ===
                last_jugement = carte.get('lastJugement', {}) if isinstance(carte.get('lastJugement'), dict) else {}
                if last_jugement and last_jugement.get('contenu'):
                    resume_parts.append("📜 DERNIER JUGEMENT")
                    resume_parts.append("─────────────────────────────────────────────")
                    resume_parts.append(f"Contenu: {last_jugement.get('contenu', 'N/A')}")
                    resume_parts.append(f"Date: {last_jugement.get('dateJugementString', 'N/A')}")
                    resume_parts.append(f"Finalité: {last_jugement.get('finalite', 'N/A')}")
                    
                    if last_jugement.get('numeroJugement'):
                        resume_parts.append(f"N° Jugement: {last_jugement.get('numeroJugement')}")
                    
                    if last_jugement.get('dateProchaineAudienceString'):
                        heure = last_jugement.get('heureProchaineAudience', '')
                        salle = last_jugement.get('roomNumberProchaineAudience', '')
                        resume_parts.append(f"Prochaine audience: {last_jugement.get('dateProchaineAudienceString')} à {heure} - Salle {salle}")
                    
                    resume_parts.append("")
                
                # === PARTIES ===
                if parties and isinstance(parties, list):
                    resume_parts.append("👥 PARTIES")
                    resume_parts.append("─────────────────────────────────────────────")
                    for i, partie in enumerate(parties, 1):
                        # Nom - flexible
                        nom = partie.get('fullName') or partie.get('nomPrenomPartie') or 'N/A'
                        
                        # Rôle - flexible
                        role = partie.get('role') or partie.get('rolePartie') or 'N/A'
                        
                        # Type personne - flexible
                        type_pers = partie.get('typePersonne') or partie.get('codeTypePersonne') or 'N/A'
                        type_label = "Personne Morale" if type_pers == 'PM' else "Personne Physique"
                        
                        resume_parts.append(f"{i}. {nom}")
                        resume_parts.append(f"   Rôle: {role} - {type_label}")
                        
                        # Compteurs optionnels
                        count_avocats = partie.get('countAvocatsPartie', 0)
                        if count_avocats and count_avocats > 0:
                            resume_parts.append(f"   Avocats: {count_avocats}")
                    
                    resume_parts.append("")
                
                # === EXPERTISES ===
                if expertises and isinstance(expertises, (list, dict)):
                    # Si c'est un dict avec une erreur, l'ignorer
                    if isinstance(expertises, dict) and expertises.get('error'):
                        pass
                    elif isinstance(expertises, list) and expertises:
                        resume_parts.append("🔬 EXPERTISES")
                        resume_parts.append("─────────────────────────────────────────────")
                        for i, expertise in enumerate(expertises, 1):
                            mission = expertise.get('libMission') or expertise.get('mission') or 'N/A'
                            resume_parts.append(f"{i}. Mission: {mission}")
                            
                            num_dossier = expertise.get('numeroDossierMI') or expertise.get('numero') or ''
                            if num_dossier:
                                resume_parts.append(f"   N° Dossier MI: {num_dossier}")
                            
                            etat = expertise.get('etatMission') or expertise.get('etat') or ''
                            if etat:
                                resume_parts.append(f"   État: {etat}")
                            
                            experts = expertise.get('experts', [])
                            if experts:
                                resume_parts.append(f"   Expert(s): {', '.join(experts)}")
                        
                        resume_parts.append("")
                
                # === DÉCISIONS RÉCENTES ===
                if decisions and isinstance(decisions, list):
                    resume_parts.append("� DERNIÈRES DÉCISIONS (5 plus récentes)")
                    resume_parts.append("─────────────────────────────────────────────")
                    for i, decision in enumerate(decisions[:5], 1):
                        # Type/finalité - flexible
                        type_dec = decision.get('finalite') or decision.get('typeDecision') or 'N/A'
                        
                        # Date - flexible
                        date_dec = decision.get('dateJugementString') or decision.get('dateTimeDecision') or 'N/A'
                        
                        # Contenu
                        contenu = decision.get('contenu') or decision.get('contenuDecision') or ''
                        
                        resume_parts.append(f"{i}. {type_dec}")
                        resume_parts.append(f"   Date: {date_dec}")
                        
                        if contenu:
                            # Limiter la longueur du contenu
                            contenu_court = contenu[:100] + "..." if len(contenu) > 100 else contenu
                            resume_parts.append(f"   Contenu: {contenu_court}")
                        
                        # Numéro jugement
                        num_jug = decision.get('numeroJugement')
                        if num_jug:
                            resume_parts.append(f"   N° Jugement: {num_jug}")
                        
                        # Prochaine audience
                        proch_aud = decision.get('dateProchaineAudienceString') or decision.get('dateTimeNextAudience')
                        if proch_aud:
                            heure = decision.get('heureProchaineAudience', '')
                            if heure:
                                resume_parts.append(f"   Prochaine audience: {proch_aud} à {heure}")
                            else:
                                resume_parts.append(f"   Prochaine audience: {proch_aud}")
                        
                        resume_parts.append("")
                
                # === STATISTIQUES ===
                resume_parts.append("📊 STATISTIQUES")
                resume_parts.append("─────────────────────────────────────────────")
                resume_parts.append(f"Nombre de parties: {len(parties) if isinstance(parties, list) else 0}")
                
                nb_expertises = len(expertises) if isinstance(expertises, list) else 0
                resume_parts.append(f"Nombre d'expertises: {nb_expertises}")
                
                resume_parts.append(f"Nombre de décisions: {len(decisions) if isinstance(decisions, list) else 0}")
                
                # Timestamp
                if data.get('timestamp'):
                    resume_parts.append(f"\n⏰ Données récupérées le: {data.get('timestamp')}")
                    resume_parts.append(f"Source: {record.data.get('source', 'N/A')}")
                
                record.resume = "\n".join(resume_parts)
                
            except Exception as e:
                _logger.error(f"Erreur lors de la génération du résumé: {str(e)}")
                record.resume = f"Erreur lors de la génération du résumé: {str(e)}"

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
            
            # Générer automatiquement le résumé après récupération
            self._compute_resume()
            
            _logger.info(f"Données du dossier {self.reference_dossier} récupérées avec succès")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✅ Succès'),
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

    def action_fill_from_json(self):
        """Remplit les champs du dossier à partir des données JSON"""
        self.ensure_one()
        
        if not self.data:
            raise UserError(_("Aucune donnée JSON disponible. Veuillez d'abord récupérer les données via l'API."))
        
        try:
            from datetime import datetime
            data = self.data
            
            # Vérifier la structure des données
            if not isinstance(data, dict) or 'data' not in data:
                raise UserError(_("Format des données JSON invalide."))
            
            api_data = data.get('data', {})
            carte = api_data.get('carte', {})
            parties_data = api_data.get('parties', [])
            decisions_data = api_data.get('decisions', [])
            
            # Remplir les champs depuis carte
            if carte:
                # Magistrat (juge rapporteur)
                if carte.get('jugeRapporteur'):
                    self.magistrat = carte.get('jugeRapporteur')
                
                # Numéro de dossier
                if carte.get('numeroCompletDossier1Instance'):
                    self.numero_dossier = carte.get('numeroCompletDossier1Instance')
            
            # Supprimer les parties existantes
            self.parties_ids.unlink()
            
            # Créer les parties - Approche flexible clé/valeur
            for partie in parties_data:
                values = {
                    'dossier_id': self.id,
                    'raw_data': partie,  # Sauvegarder TOUTES les données JSON
                }
                
                # Extraction intelligente : essayer différents noms de champs possibles
                # ID Partie
                for key in ['idPartie', 'idPartieDossier', 'id', 'id_partie']:
                    if key in partie and partie[key]:
                        values['id_partie'] = partie[key]
                        break
                
                # Nom et Prénom
                for key in ['nomPrenomPartie', 'fullName', 'nom', 'name', 'nom_prenom']:
                    if key in partie and partie[key]:
                        values['nom_prenom'] = partie[key]
                        break
                
                # Rôle
                for key in ['rolePartie', 'role', 'qualite']:
                    if key in partie and partie[key]:
                        values['role'] = partie[key]
                        break
                
                # Type de Personne
                for key in ['codeTypePersonne', 'typePersonne', 'type', 'type_personne']:
                    if key in partie and partie[key]:
                        values['type_personne'] = partie[key]
                        break
                
                # Compteurs (optionnels)
                for key in ['countAvocatsPartie', 'count_avocats', 'avocats']:
                    if key in partie:
                        values['count_avocats'] = partie[key] or 0
                        break
                
                for key in ['countMandatairesPartie', 'count_mandataires', 'mandataires']:
                    if key in partie:
                        values['count_mandataires'] = partie[key] or 0
                        break
                
                for key in ['countHuissiersPartie', 'count_huissiers', 'huissiers']:
                    if key in partie:
                        values['count_huissiers'] = partie[key] or 0
                        break
                
                for key in ['countRepresentantsPartie', 'count_representants', 'representants']:
                    if key in partie:
                        values['count_representants'] = partie[key] or 0
                        break
                
                self.env['expertise.partie'].create(values)
            
            # Supprimer les décisions existantes
            self.decisions_ids.unlink()
            
            # Créer les décisions et trouver la prochaine audience - Approche flexible
            prochaine_audience = None
            for decision in decisions_data:
                values = {
                    'dossier_id': self.id,
                    'raw_data': decision,  # Sauvegarder TOUTES les données JSON
                }
                
                # Extraction intelligente des champs
                # ID Décision
                for key in ['idDecision', 'id', 'id_decision']:
                    if key in decision and decision[key]:
                        values['id_decision'] = decision[key]
                        break
                
                # Type de Décision
                for key in ['typeDecision', 'type', 'finalite']:
                    if key in decision and decision[key]:
                        values['type_decision'] = decision[key]
                        break
                
                # Contenu
                for key in ['contenuDecision', 'contenu', 'content', 'description']:
                    if key in decision and decision[key]:
                        values['contenu_decision'] = decision[key]
                        break
                
                # Numéro Jugement
                for key in ['numeroJugement', 'numero', 'numero_jugement']:
                    if key in decision and decision[key]:
                        values['numero_jugement'] = str(decision[key])
                        break
                
                # Dates - Support de plusieurs formats
                date_decision = None
                for key in ['dateTimeDecision', 'dateJugementString', 'date_decision', 'date']:
                    date_str = decision.get(key, '')
                    if date_str:
                        try:
                            # Essayer format datetime
                            date_decision = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
                            values['date_time_decision'] = date_decision
                            break
                        except:
                            try:
                                # Essayer format date seule
                                date_decision = datetime.strptime(date_str, "%d/%m/%Y")
                                values['date_time_decision'] = date_decision
                                break
                            except:
                                pass
                
                date_next_audience = None
                for key in ['dateTimeNextAudience', 'dateProchaineAudienceString', 'prochaine_audience']:
                    date_next_str = decision.get(key, '')
                    if date_next_str:
                        # Récupérer aussi l'heure si disponible
                        heure = decision.get('heureProchaineAudience', '09:00')
                        date_avec_heure = f"{date_next_str} {heure}"
                        try:
                            date_next_audience = datetime.strptime(date_avec_heure, "%d/%m/%Y %H:%M")
                            values['date_time_next_audience'] = date_next_audience
                            if not prochaine_audience or date_next_audience < prochaine_audience:
                                prochaine_audience = date_next_audience
                            break
                        except:
                            try:
                                date_next_audience = datetime.strptime(date_next_str, "%d/%m/%Y")
                                values['date_time_next_audience'] = date_next_audience
                                if not prochaine_audience or date_next_audience < prochaine_audience:
                                    prochaine_audience = date_next_audience
                                break
                            except:
                                pass
                
                # Dates DE et NA (optionnelles)
                for key in ['dateDe', 'date_de']:
                    date_de_str = decision.get(key, '')
                    if date_de_str:
                        try:
                            date_de = datetime.strptime(date_de_str, "%d/%m/%Y").date()
                            values['date_de'] = date_de
                            break
                        except:
                            pass
                
                for key in ['dateNA', 'date_na']:
                    date_na_str = decision.get(key, '')
                    if date_na_str:
                        try:
                            date_na = datetime.strptime(date_na_str, "%d/%m/%Y").date()
                            values['date_na'] = date_na
                            break
                        except:
                            pass
                
                self.env['expertise.decision'].create(values)
            
            if prochaine_audience:
                self.date_prochaine_audience = prochaine_audience
            
            _logger.info(f"Champs du dossier {self.reference_dossier} remplis depuis les données JSON")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✅ Succès'),
                    'message': _('Les champs du dossier ont été remplis à partir des données JSON.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            error_msg = f"Erreur lors du remplissage des champs: {str(e)}"
            _logger.error(error_msg)
            raise UserError(_(error_msg))


