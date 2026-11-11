{
    "name": "Global Record Search",
    "version": "20.0.1.5.0",
    "category": "Productivity",
    "summary": "Search business records from Odoo's built-in command palette",
    "description": """
Search business records from Odoo's built-in Ctrl+K command palette and its
slash namespace. Results use the current user's access restrictions and
active company context.
    """,
    "author": "Shuhaife Binhamza",
    "website": "https://shuhaife.pages.dev",
    "license": "LGPL-3",
    "depends": ["web", "web_enterprise"],
    "data": [
        "security/ir.access.csv",
        "views/global_search_config_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "global_record_search/static/src/js/command_palette_provider.js",
            "global_record_search/static/src/js/palette_animation.js",
            "global_record_search/static/src/scss/global_record_search.scss",
        ],
    },
    "installable": True,
    "application": False,
}
