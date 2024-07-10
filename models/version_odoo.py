from odoo import fields, models, api

class OdooVersion(models.Model):
    _name = "odoo.version"
    _description = "specify the odoo version for the formations"

    name = fields.Char(string="Odoo version", translate=True, required=True)