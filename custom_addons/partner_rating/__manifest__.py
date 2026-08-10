# -*- coding: utf-8 -*-
{
    'name': 'Calificadora de Proveedores',
    'version': '17.0.6.7.0',
    'category': 'Purchases',
    'summary': 'Evaluación de proveedores con checklist por tipo de persona',
    'description': """
Evalúa contactos/proveedores:
- Datos del contacto (capturados al digitalizar documentos)
- Checklist de documentos según Persona Moral / Física
- Criterios, pesquisas, riesgo y calificación
""",
    'depends': ['base', 'contacts', 'partner_documents'],
    'data': [
        'security/evaluation_security.xml',
        'security/ir.model.access.csv',
        'wizard/partner_rating_score_help_wizard_views.xml',
        'views/partner_rating_views.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
