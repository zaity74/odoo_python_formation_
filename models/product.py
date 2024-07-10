# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.tools.float_utils import float_round
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template',

    formation_id = fields.Many2one(
        'formation.phi.bis', 'Formation', company_dependent=True,
        domain="[('company_id', '=', current_company_id)]",
        help='Select a billable project on which tasks can be created. This setting must be set for each company.')

    create_formation = fields.Selection(
        selection=[
            ('formation', 'Formations'),
        ],
        string="Create a formation", default='formation',
        help="On Sales order confirmation, this product can generate a formation. \
           From those, you can track the service you are selling.\n \
           'In sale order\'s project': Will use the sale order\'s configured project if defined or fallback to \
           creating a new project based on the selected template.")

