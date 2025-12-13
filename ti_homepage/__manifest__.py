{
    "name": "TI Homepage",
    "summary": "صفحة رئيسية عربية مخصصة لموقع التقوى",
    "version": "19.0.1.0.0",
    "category": "Website",
    "author": "TI Team",
    "website": "https://altaqwa-islamic.org/",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "data/website_logo.xml",
        "views/ti_homepage_views.xml",
        # "views/ti_contact_about.xml",
        "views/ti_contact_lead_inherit.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "ti_homepage/static/src/scss/ti_homepage.scss",
        ],
    },
    "installable": True,
    "application": False,
}
