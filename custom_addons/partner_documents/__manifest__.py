# -*- coding: utf-8 -*-
{
    'name': 'Partner Documents',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Pestaña de documentos en contactos',
    'description': """
Agrega la pestaña Documentos junto a Notas Internas en la ficha de contacto.
Permite anexar PDF, imágenes y Excel con nombre y vista previa.
""",
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
