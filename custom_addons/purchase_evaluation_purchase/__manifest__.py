# -*- coding: utf-8 -*-
{
    'name': 'Evaluación de Compras - Enlace purchase.order',
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Botón y enlace de evaluación de compra en pedidos estándar de Odoo',
    'description': """
Puente opcional hacia purchase.order.
Instalar solo si usan el módulo Compras estándar de Odoo.
Para requisiciones custom de producción, use link_to_record / create_from_record.
""",
    'depends': ['purchase', 'purchase_evaluation'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
