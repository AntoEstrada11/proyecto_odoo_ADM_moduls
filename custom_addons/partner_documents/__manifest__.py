# -*- coding: utf-8 -*-
{
    'name': 'Partner Documents',
    'version': '17.0.3.6.0',
    'category': 'Sales/CRM',
    'summary': 'Documentos digitalizados de proveedores con captura de datos',
    'description': """
Pestaña Documentos en contactos:
- Tipos de documento por Persona Moral / Física
- Wizard al subir que captura datos del contacto
- Vista previa de archivos
- Documentos confidenciales restringidos por grupo/bandera de usuario
""",
    'depends': ['base', 'contacts'],
    'data': [
        'security/partner_documents_security.xml',
        'security/ir.model.access.csv',
        'data/partner_document_type_data.xml',
        'wizard/partner_document_upload_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
