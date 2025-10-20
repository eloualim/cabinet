# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Avocat(models.Model):
    _name = 'avocat'
    _description = 'Avocat'
    
    # Champs de base
    name = fields.Char(
        string='Nom de l\'avocat',
        required=True,
        help='Nom de l\'avocat'
    )
    
    arabic_name = fields.Char(
        string='Nom Arabe',
        help='Nom de l\'avocat en arabe'
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