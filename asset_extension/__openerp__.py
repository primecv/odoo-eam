# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2015 Prime Consulting, Cape Verde (<http://prime.cv>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Assets Extension',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Asset Management',
    'author': 'Prime Consulting, Cape Verde',
    'website': 'prime.cv',
    'category': 'Enterprise Asset Management',
    'depends': ['mro', 'res_partner_hospital', 'hr', 'asset_stock', 'asset_mrp'],
    'data': [
        'asset_view.xml',
        'product_view.xml',
        'asset_sequence.xml',
        'asset_data.xml',
        'res_partner_view.xml',
        'hr_view.xml',
        'mro_view.xml',
        'asset_stock_view.xml',
        'stock_view.xml',
        'stock_data.xml',
        'asset_mrp_view.xml',
        'report/layouts.xml',
        'data/report_paperformat.xml',
        'asset_report.xml',
        'asset_report_view.xml',
        'mro_report.xml',
        'views/report_mroperiod.xml',
        'views/report_mroscheduled.xml',
        'views/report_mrotechnician.xml',
        'views/report_assetlist.xml',
        'wizard/asset_asset_new_barcode_view.xml',
        'wizard/asset_list_view.xml',
        'wizard/mro_hcv_report_view.xml',
        'views/report_equipments.xml',
        'views/report_stock_move.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
