"""
Bridge module between Oscar and the core Avalara functionality
"""
import logging
import datetime
from decimal import Decimal as D
import zlib

from django.core.cache import cache
from django.conf import settings

from . import gateway

__all__ = ['apply_taxes', 'submit', 'fetch_tax_info']

logger = logging.getLogger('avalara')


def apply_taxes(user, basket, shipping_address, shipping_method):
    """
    Apply taxes to the basket and shipping method
    """
    data = fetch_tax_info(user, basket, shipping_address, shipping_method)

    # Build hash table of line_id => tax and apply to basket lines
    line_taxes = {}
    for tax_line in data['TaxLines']:
        line_taxes[tax_line['LineNo']] = D(tax_line['Tax'])

    # Apply these tax values to the basket and shipping
    # method.
    for line in basket.all_lines():
        line.stockinfo.price.tax = line_taxes[str(line.id)]
    shipping_method.tax = line_taxes['SHIPPING']


def submit(order):
    """
    Submit tax information from an order
    """
    payload = _build_payload(
        'SalesInvoice',
        order.number,
        order.user,
        order.lines.all(),
        order.shipping_address,
        order.shipping_method,
        order.shipping_excl_tax,
        commit=True)
    gateway.post_tax(payload)


def fetch_tax_info_for_order(order):
    """
    Fetch tax info retrospectively for order.

    This is for debugging tax issues.
    """
    payload = _build_payload(
        'SalesOrder',
        order.number,
        order.user, order.lines.all(),
        order.shipping_address,
        order.shipping_method,
        order.shipping_excl_tax,
        commit=False)
    gateway.post_tax(payload)


def fetch_tax_info(user, basket, shipping_address, shipping_method):
    # Look for a cache hit first
    payload = _build_payload(
        'SalesOrder', 'basket-%d' % basket.id,
        user, basket.all_lines(), shipping_address,
        unicode(shipping_method.name), shipping_method.charge_excl_tax,
        commit=False)
    key = _build_cache_key(payload)
    data = cache.get(key)
    if not data:
        logger.debug("Cache miss - fetching data")
        data = gateway.post_tax(payload)
        cache.set(key, data, timeout=None)
    else:
        logger.debug("Cache hit")
    return data


def _build_payload(doc_type, doc_code, user, lines, shipping_address,
                   shipping_method, shipping_charge, commit):
    payload = {}

    # Use a single company code for now
    payload['CompanyCode'] = settings.AVALARA_COMPANY_CODE

    payload['DocDate'] = datetime.date.today().strftime("%Y-%m-%d")
    if user and user.id:
        payload['CustomerCode'] = 'customer-%d' % user.id
    else:
        payload['CustomerCode'] = 'anonymous'
    payload['DocCode'] = doc_code
    payload['DocType'] = doc_type
    payload['DetailLevel'] = 'Line'
    payload['Commit'] = commit
    payload['Lines'] = []
    payload['Addresses'] = []

    # Customer address
    address_code = shipping_address.generate_hash()
    address = {
        'AddressCode': address_code,
        'Line1': shipping_address.line1,
        'Line2': shipping_address.line2,
        'Line3': shipping_address.line3,
        'City': shipping_address.city,
        'Region': shipping_address.state,
        'PostalCode': shipping_address.postcode,
    }
    payload['Addresses'].append(address)

    # Lines
    partner_address_codes = []
    for line in lines:
        product = line.product
        record = line.stockrecord

        # Ensure origin address in in Addresses collection
        partner_address = record.partner.primary_address
        partner_address_code = partner_address.generate_hash()
        if partner_address_code not in partner_address_codes:
            payload['Addresses'].append({
                'AddressCode': partner_address_code,
                'Line1': partner_address.line1,
                'Line2': partner_address.line2,
                'Line3': partner_address.line3,
                'City': partner_address.city,
                'Region': partner_address.state,
                'PostalCode': partner_address.postcode,
            })
            partner_address_codes.append(partner_address_code)

        # Ensure the origin address is in the Addresses collection
        line = {
            'LineNo': line.id,
            'DestinationCode': address_code,
            'OriginCode': partner_address_code,
            'ItemCode': record.partner_sku,
            'Description': product.description[:255],
            'Qty': line.quantity,
            'Amount': str(line.line_price_excl_tax),
        }
        payload['Lines'].append(line)

    # Shipping (treated as another line).  We assume origin address is the
    # first partner address
    line = {
        'LineNo': 'SHIPPING',
        'DestinationCode': address_code,
        'OriginCode': partner_address_codes[0],
        'ItemCode': '',
        'Description': shipping_method,
        'Qty': 1,
        'Amount': str(shipping_charge),
        'TaxCode': 'FR',  # Special code for shipping
    }
    payload['Lines'].append(line)

    return payload


def _build_cache_key(payload):
    """
    Build a caching key based on a given payload.  The key should change if any
    part of the basket or shipping address changes.
    """
    parts = []

    for address in payload['Addresses']:
        parts.append(str(address['AddressCode']))

    for line in payload['Lines']:
        parts.extend([line['Amount'], line['ItemCode'], str(line['Qty'])])

    return "avalara-%s" % zlib.crc32("-".join(parts))