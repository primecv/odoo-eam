# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2011-2012 Camptocamp SA
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
{'name': 'Geospatial support of Assets',
 'version': '0.1',
 'category': 'GeoBI',
 'author': "Camptocamp,Odoo Community Association (OCA),Prime Consulting",
 'license': 'AGPL-3',
 'website': 'http://prime.cv',
 'depends': [
     'base_geoengine',
	 'asset_extension',
 ],
 'data': [
	 'stock_view.xml',
     'geo_asset_view.xml'
 ],
 'installable': True,
 'application': False,
 'active': False,
 }
