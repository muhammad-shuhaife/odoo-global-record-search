import logging

from odoo import api, models, tools
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

PARAM_LIMIT = "global_record_search.limit"
PARAM_MIN_CHARS = "global_record_search.min_chars"
DEFAULT_LIMIT = 5
DEFAULT_MIN_CHARS = 3
BATCH_SIZE = 12  # models searched per RPC, so the first hits show quickly
DEFAULT_PRIORITY = 100

# Searched first, in this order, unless a setting overrides the priority.
PRIORITY_MODELS = [
    "res.partner",
    "product.template",
    "sale.order",
    "purchase.order",
    "account.move",
    "crm.lead",
    "project.task",
    "hr.employee",
    "stock.picking",
]

# Technical models that show up in menus (mostly in debug mode) but are
# never what a person is looking for.
SKIPPED_PREFIXES = (
    "ir.", "base.", "base_import.", "bus.", "mail.", "web.", "auth.",
    "report.", "iap.", "sms.", "digest.", "res.config", "res.users.log",
)

# First non-empty one is shown as the second line of a result.
SUBTITLE_FIELDS = (
    "email", "default_code", "ref", "client_order_ref",
    "partner_id", "phone", "mobile",
)


class GlobalSearch(models.AbstractModel):
    _name = "global.search"
    _description = "Global Record Search"

    # ------------------------------------------------------------------
    # Model discovery
    # ------------------------------------------------------------------
    @api.model
    @tools.ormcache("self.env.uid")
    def _get_menu_models(self):
        """Models the current user can reach through a visible menu and read."""
        menus = self.env["ir.ui.menu"].search([("action", "!=", False)])
        action_ids = []
        for vals in menus.read(["action"]):
            model_name, _sep, res_id = (vals["action"] or "").partition(",")
            if model_name == "ir.actions.act_window" and res_id:
                action_ids.append(int(res_id))
        actions = self.env["ir.actions.act_window"].sudo().browse(action_ids).exists()
        result = []
        for res_model in dict.fromkeys(actions.mapped("res_model")):
            if not res_model or res_model not in self.env:
                continue
            if res_model.startswith(SKIPPED_PREFIXES):
                continue
            Model = self.env[res_model]
            if Model._transient or Model._abstract:
                continue
            if not Model.has_access("read"):
                continue
            result.append(res_model)
        return tuple(result)

    @api.model
    def _get_priority(self, model_name, configs):
        if model_name in configs:
            return configs[model_name].priority
        if model_name in PRIORITY_MODELS:
            return PRIORITY_MODELS.index(model_name)
        return DEFAULT_PRIORITY

    # ------------------------------------------------------------------
    # Public entry point (called from the home menu)
    # ------------------------------------------------------------------
    @api.model
    def search_records(self, term, batch=0):
        """Search `term` in one batch of models.

        Returns {'groups': [...], 'has_next': bool}. The client keeps calling
        with batch + 1 while has_next is true.
        """
        term = (term or "").strip()
        config_parameters = self.env["ir.config_parameter"].sudo()
        min_chars = config_parameters.get_int(PARAM_MIN_CHARS, DEFAULT_MIN_CHARS)
        limit = config_parameters.get_int(PARAM_LIMIT, DEFAULT_LIMIT)
        if len(term) < min_chars:
            return {"groups": [], "has_next": False}

        configs = {
            config.model_id.model: config
            for config in self.env["global.search.config"].sudo().search([])
        }
        model_names = [
            name for name in self._get_menu_models()
            if not (name in configs and configs[name].exclude)
        ]
        model_names.sort(key=lambda name: self._get_priority(name, configs))

        start = max(int(batch), 0) * BATCH_SIZE
        groups = []
        for name in model_names[start:start + BATCH_SIZE]:
            group = self._search_model(name, term, limit, configs.get(name))
            if group:
                groups.append(group)
        return {"groups": groups, "has_next": start + BATCH_SIZE < len(model_names)}

    # ------------------------------------------------------------------
    # Per-model search
    # ------------------------------------------------------------------
    @api.model
    def _get_term_domain(self, Model, term, config=None):
        """Build a client-serializable display-name domain plus extra fields.

        Calling ``_search_display_name`` directly can return an internal
        ``DomainCustom`` (for example, product variants on ``product.template``).
        That works for ORM searches but cannot be sent back to the browser for
        the "See all" action. Searching the ``display_name`` field delegates
        to the same model search method while keeping the action domain plain.
        """
        if Model._rec_name or Model._rec_names_search:
            base = [("display_name", "ilike", term)]
        else:
            base = []
        extra = []
        if config:
            for field in config.extra_field_ids:
                if field.name in Model._fields and Model._fields[field.name].store:
                    extra.append([(field.name, "ilike", term)])
        if base and extra:
            return Domain.OR([base] + extra)
        if base:
            return base
        if extra:
            return Domain.OR(extra)
        return []  # nothing searchable: skip instead of matching everything

    @api.model
    def _search_model(self, model_name, term, limit, config=None):
        Model = self.env[model_name]
        domain = self._get_term_domain(Model, term, config)
        if not domain:
            return None
        try:
            with self.env.cr.savepoint():
                records = Model.search(domain, limit=limit + 1)
                if not records:
                    return None
                return {
                    "model": model_name,
                    "label": Model._description or model_name,
                    "records": [self._record_vals(rec) for rec in records[:limit]],
                    "has_more": len(records) > limit,
                    "domain": list(domain),
                }
        except Exception:  # noqa: BLE001
            _logger.debug("Global search skipped %s", model_name, exc_info=True)
            return None

    @api.model
    def _record_vals(self, record):
        try:
            name = record.display_name
        except Exception:  # noqa: BLE001
            name = ""
        return {
            "id": record.id,
            "name": name or "%s #%s" % (record._description, record.id),
            "subtitle": self._get_subtitle(record),
        }

    @api.model
    def _get_subtitle(self, record):
        for fname in SUBTITLE_FIELDS:
            field = record._fields.get(fname)
            if not field:
                continue
            try:
                value = record[fname]
            except Exception:  # noqa: BLE001 - field restricted by groups
                continue
            if field.type == "many2one":
                value = value.display_name
            if value:
                return str(value)
        return ""
