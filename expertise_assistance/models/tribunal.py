# -*- coding: utf-8 -*-

from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class Tribunal(models.Model):
    _name = "tribunal"
    _description = "Tribunal"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(
        string="Nom du Tribunal",
        required=True,
        help="Nom du tribunal en français"
    )

    ar_name = fields.Char(
        string="Nom Arabe",
        help="Nom du tribunal en arabe"
    )

    idJuridiction = fields.Char(
        string="ID Juridiction",
        help="Identifiant de la juridiction"
    )

    parent_id = fields.Many2one(
        'tribunal',
        string="Parent",
        ondelete='restrict',
        domain="[('CA', '=', True)]",
        help="Tribunal parent (pour les hiérarchies)"
    )

    ville_id = fields.Many2one(
        'ville',
        string="Ville",
        ondelete='restrict',
        help="Ville où se trouve le tribunal"
    )

    CA = fields.Boolean(
        string="CA (Cour d'Appel)",
        default=False,
        help="Indique si c'est une Cour d'Appel"
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Décocher pour archiver le tribunal"
    )

    _sql_constraints = [
        ('idjuridiction_unique', 
         'UNIQUE(idJuridiction)', 
         'L\'ID Juridiction doit être unique!'),
        ('name_unique', 
         'UNIQUE(name)', 
         'Ce nom de tribunal existe déjà!'),
    ]
