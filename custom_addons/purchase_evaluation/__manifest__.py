# -*- coding: utf-8 -*-
{
    'name': 'Evaluación de Compras / Requisiciones',
    'version': '17.0.1.2.0',
    'category': 'Purchases',
    'summary': 'Documentación y evaluación por compra/requisición, enlazable a Compras',
    'description': """
Evaluación de cada compra/requisición en dos fases:
1. Adjuntar y validar documentación de la requisición
2. Evaluar la compra (solo si la documentación está lista)

Enlace a producción:
- purchase.order (si el módulo purchase está instalado)
- Campos source_model / source_res_id / source_ref para ligar
  cualquier requisición o compra custom de producción.
""",
    'depends': ['base', 'contacts', 'mail', 'partner_documents', 'partner_rating'],
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_evaluation_document_type_data.xml',
        'views/purchase_evaluation_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
