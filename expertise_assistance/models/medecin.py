# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Medecin(models.Model):
    _name = 'medecin'
    _description = 'Médecin'
    
    # Champs de base
    name = fields.Char(
        string='Nom du médecin',
        required=True,
        help='Nom du médecin'
    )
    
    arabic_name = fields.Char(
        string='Nom Arabe',
        help='Nom du médecin en arabe'
    )
    
    phone = fields.Char(
        string='Téléphone',
        help='Numéro de téléphone'
    )
    
    mobile = fields.Char(
        string='Mobile',
        help='Numéro de téléphone mobile'
    )
    
    email = fields.Char(
        string='Email',
        help='Adresse email'
    )
    
    street = fields.Char(
        string='Rue',
        help='Adresse - Rue'
    )
    
    street2 = fields.Char(
        string='Rue 2',
        help='Adresse - Complément'
    )
    
    zip = fields.Char(
        string='Code postal',
        help='Code postal'
    )
    
    city = fields.Char(
        string='Ville',
        help='Ville'
    )
    
    state_id = fields.Many2one(
        'res.country.state',
        string='État/Province',
        help='État ou province'
    )
    
    country_id = fields.Many2one(
        'res.country',
        string='Pays',
        help='Pays'
    )