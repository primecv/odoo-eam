# -*- coding: utf-8 -*-
##############################################################################
#
#    Prime Consulting, Cape Verde
#    Copyright (C) 2016 Prime Consulting (<http://www.prime.cv>).
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

from openerp.osv import fields, osv

class lang(osv.osv):
	_inherit = "res.lang"

	def set_date_format(self, cr, uid, **args):
		langs = self.search(cr, uid, [('id','>',0)])
		for lang in self.read(cr, uid, langs, ['id']):
			self.write(cr, uid, [lang['id']], {'date_format': '%d/%m/%Y'})
		return True

