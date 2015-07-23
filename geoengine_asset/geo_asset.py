# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Prime Consulting, Cape Verde
#    Copyright 2011-2012 Prime Consulting, Cape Verde <htttp://prime.cv/>
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

# -*- coding: utf-8 -*-

try:
    import simplejson as json
except ImportError:
    import json
import urllib

from openerp import api
import logging
from openerp import exceptions
from openerp import tools
from openerp.tools.translate import _

from openerp.addons.base_geoengine import geo_model
from openerp.addons.base_geoengine import fields

from openerp.osv import osv, fields as osv_fields
from openerp import fields as oe_fields

try:
   import requests
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning('requests is not available in the sys path')

_logger = logging.getLogger(__name__)


def geo_find(addr):
    url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='
    url += urllib.quote(addr.encode('utf8'))

    try:
        result = json.load(urllib.urlopen(url))
    except Exception, e:
        raise osv.except_osv(_('Network error'),
                             _('Cannot contact geolocation servers. Please make sure that your internet connection is up and running (%s).') % e)
    if result['status'] != 'OK':
        return None

    try:
        geo = result['results'][0]['geometry']['location']
        return float(geo['lat']), float(geo['lng'])
    except (KeyError, ValueError):
        return None


def geo_query_address(street=None, zip=None, city=None, county=None, country=None):
    if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
        # put country qualifier in front, otherwise GMap gives wrong results,
        # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of the Congo'
        country = '{1} {0}'.format(*country.split(',', 1))
    return tools.ustr(', '.join(filter(None, [street,
                                              ("%s %s" % (zip or '', city or '')).strip(),
                                              county,
                                              country])))

class asset_asset(geo_model.GeoModel, osv.osv):
    _inherit = "asset.asset"


    @api.one
    def geocode_address(self):
        """Get the latitude and longitude by requesting "mapquestapi"
        see http://open.mapquestapi.com/geocoding/
        """
        url = 'http://nominatim.openstreetmap.org/search'
        pay_load = {
            'limit': 1,
            'format': 'json',
  			'street': self.street or '',
            'postalCode': self.zip or '',
            'city': self.city or '',
			'county': self.county or '',
            'country': self.country and self.country.name or '',
            'countryCodes': self.country and self.country.code or ''}

        request_result = requests.get(url, params=pay_load)
        try:
            request_result.raise_for_status()
        except Exception as e:
            _logger.exception('Geocoding error')
            raise exceptions.Warning(_(
                'Geocoding error. \n %s') % e.message)
        vals = request_result.json()
        vals = vals and vals[0] or {}
        self.write({
            'latitude': vals.get('lat'),
            'longitude': vals.get('lon'),
            })

    @api.one
    def geo_localize(self):
        self.geocode_address()
        return True

    @api.one
    @api.depends('latitude', 'longitude')
    def _get_geo_point(self):
        if not self.latitude or not self.longitude:
            self.geo_point = False
        else:
            self.geo_point = fields.GeoPoint.from_latlon(
                self.env.cr, self.latitude, self.longitude)

    geo_point = fields.GeoPoint(string='Addresses Coordinate', readonly=True, store=True, compute='_get_geo_point')
    street = oe_fields.Char(string='Street', related='property_stock_asset.street', store=True, readonly=True)
    city = oe_fields.Char(string='City', related='property_stock_asset.city', store=True, readonly=True)
    zip = oe_fields.Char(string='Zip', related='property_stock_asset.zip', store=True, readonly=True)
    country = oe_fields.Many2one('res.country', string='Country', related='property_stock_asset.country', store=True, readonly=True)
    island = oe_fields.Char(string='Island', related='property_stock_asset.island', store=True, readonly=True)
    county = oe_fields.Char(string='County', related='property_stock_asset.county', store=True, readonly=True)
    latitude = oe_fields.Float(string='Latitude', related='property_stock_asset.latitude', store=True, readonly=True)
    longitude = oe_fields.Float(string='Longitude', related='property_stock_asset.longitude', store=True, readonly=True)

    def geo_localize(self, cr, uid, ids, context=None):
        for product in self.browse(cr, uid, ids):
            if not product:
                continue
            result = geo_find(geo_query_address(street=product.street,
                                                zip=product.zip,
                                                city=product.city,
												county=product.county,
                                                country=product.country.name))
            if result:
                self.write(cr, uid, [product.id], {
                    'latitude': result[0],
                    'longitude': result[1],
                }, context=context)
        return True

    @api.one
    @api.depends('property_stock_asset')
    def onchange_location(self, location_id=False):
        if location_id:
           location = self.env['stock.location'].browse(location_id)
           return {
              'value': {
                  'street': location.street,
  				  'city': location.city,
				  'zip': location.zip,
			 	  'country': location.country.id or False,
         		  'island': location.island,
				  'county': location.county,
                  'latitude': location.latitude,
				  'longitude': location.longitude
               }
            }
        return {} 

