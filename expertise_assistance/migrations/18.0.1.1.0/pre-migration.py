# -*- coding: utf-8 -*-
"""
Migration pour ajouter les champs raw_data aux parties et décisions
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Ajoute les colonnes raw_data si elles n'existent pas déjà
    """
    _logger.info("=== Début migration 18.0.1.1.0 ===")
    
    # Vérifier et ajouter raw_data pour expertise_partie
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='expertise_partie' AND column_name='raw_data'
    """)
    if not cr.fetchone():
        _logger.info("Ajout de la colonne raw_data à expertise_partie")
        cr.execute("""
            ALTER TABLE expertise_partie 
            ADD COLUMN raw_data jsonb
        """)
    
    # Vérifier et ajouter raw_data pour expertise_decision
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='expertise_decision' AND column_name='raw_data'
    """)
    if not cr.fetchone():
        _logger.info("Ajout de la colonne raw_data à expertise_decision")
        cr.execute("""
            ALTER TABLE expertise_decision 
            ADD COLUMN raw_data jsonb
        """)
    
    _logger.info("=== Fin migration 18.0.1.1.0 ===")
