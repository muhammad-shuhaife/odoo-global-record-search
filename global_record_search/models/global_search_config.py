from odoo import fields, models


class GlobalSearchConfig(models.Model):
    _name = "global.search.config"
    _description = "Global Search Model Settings"
    _rec_name = "model_id"
    _order = "priority, id"

    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        required=True,
        ondelete="cascade",
        index=True,
    )
    exclude = fields.Boolean(
        string="Exclude from search",
        help="Never search this model (useful for heavy tables such as logs).",
    )
    priority = fields.Integer(
        default=100,
        help="Lower numbers are searched and shown first.",
    )
    extra_field_ids = fields.Many2many(
        "ir.model.fields",
        "global_search_config_field_rel",
        "config_id",
        "field_id",
        string="Extra search fields",
        domain="[('model_id', '=', model_id), ('store', '=', True), ('ttype', 'in', ['char', 'text'])]",
        help="Searched in addition to the fields Odoo already uses for the name search "
             "(for example the barcode on products).",
    )

    _sql_constraints = [
        ("model_uniq", "unique(model_id)", "This model already has a search setting."),
    ]
