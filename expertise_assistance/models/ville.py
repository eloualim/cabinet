# -*- coding: utf-8 -*-

from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class Ville(models.Model):
    _name = "ville"
    _description = "Ville"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(
        string="Nom de la Ville",
        required=True,
        help="Nom de la ville en français"
    )

    ar_name = fields.Char(
        string="Nom Arabe",
        help="Nom de la ville en arabe"
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Décocher pour archiver la ville"
    )

    _sql_constraints = [
        ('name_unique', 
         'UNIQUE(name)', 
         'Ce nom de ville existe déjà!'),
    ]
