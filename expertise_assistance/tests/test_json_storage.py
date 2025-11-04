# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la sauvegarde des données JSON
"""

import logging

_logger = logging.getLogger(__name__)


def test_json_save(env):
    """
    Test la sauvegarde des données JSON dans parties et décisions
    """
    
    # Données de test
    test_partie = {
        'idPartie': 999,
        'nomPrenomPartie': 'Test Personne',
        'rolePartie': 'مدعي',
        'codeTypePersonne': 'PP',
        'countAvocatsPartie': 2,
        'champInconnu1': 'Valeur test 1',
        'champInconnu2': 'Valeur test 2',
        'objetImbriqué': {
            'sous_champ1': 'valeur',
            'sous_champ2': 123
        }
    }
    
    test_decision = {
        'idDecision': 888,
        'typeDecision': 'Test',
        'dateTimeDecision': '01/11/2025 10:00',
        'contenuDecision': 'Contenu test',
        'champCustom': 'Valeur custom',
        'listeData': [1, 2, 3]
    }
    
    # Créer un dossier de test
    dossier = env['expertise.assistance'].create({
        'numero_dossier': 'TEST/001',
        'numero_dossier_mahakim': 'TEST001'
    })
    
    _logger.info(f"Dossier créé: {dossier.id}")
    
    # Créer une partie avec raw_data
    partie = env['expertise.partie'].create({
        'dossier_id': dossier.id,
        'id_partie': test_partie.get('idPartie'),
        'nom_prenom': test_partie.get('nomPrenomPartie'),
        'role': test_partie.get('rolePartie'),
        'type_personne': test_partie.get('codeTypePersonne'),
        'count_avocats': test_partie.get('countAvocatsPartie'),
        'raw_data': test_partie
    })
    
    _logger.info(f"Partie créée: {partie.id}")
    _logger.info(f"Raw data partie: {partie.raw_data}")
    
    # Créer une décision avec raw_data
    decision = env['expertise.decision'].create({
        'dossier_id': dossier.id,
        'id_decision': test_decision.get('idDecision'),
        'type_decision': test_decision.get('typeDecision'),
        'contenu_decision': test_decision.get('contenuDecision'),
        'raw_data': test_decision
    })
    
    _logger.info(f"Décision créée: {decision.id}")
    _logger.info(f"Raw data décision: {decision.raw_data}")
    
    # Vérifier que les données sont bien sauvegardées
    if partie.raw_data:
        _logger.info("✅ SUCCESS: raw_data de la partie est sauvegardé")
        _logger.info(f"Champs disponibles: {list(partie.raw_data.keys())}")
    else:
        _logger.error("❌ ERREUR: raw_data de la partie est vide")
    
    if decision.raw_data:
        _logger.info("✅ SUCCESS: raw_data de la décision est sauvegardé")
        _logger.info(f"Champs disponibles: {list(decision.raw_data.keys())}")
    else:
        _logger.error("❌ ERREUR: raw_data de la décision est vide")
    
    return {
        'dossier_id': dossier.id,
        'partie_id': partie.id,
        'decision_id': decision.id
    }
