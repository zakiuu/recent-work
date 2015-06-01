# -*- coding: utf-8 -*-
import logging

from openerp import http
from openerp.http import request

_logger = logging.getLogger(__name__)


class TripController(http.Controller):

    @http.route(['/trip/web/'], type='http', auth='user')
    def a(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/trip/web')

        return request.render('kms_transport.trip_index')


    @http.route(['/transport/web/'], type='http', auth='user')
    def b(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/transport/web')

        return request.render('kms_stock.stock_transport_index')