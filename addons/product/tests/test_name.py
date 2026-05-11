# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestName(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_name = 'Product Test Name'
        cls.product_code = 'PTN'
        cls.product = cls.env['product.product'].create({
            'name': cls.product_name,
            'default_code': cls.product_code,
        })

    def test_10_product_name(self):
        display_name = self.product.display_name
        self.assertEqual(display_name, "[%s] %s" % (self.product_code, self.product_name),
                         "Code should be preprended the name as the context is not preventing it.")
        display_name = self.product.with_context(display_default_code=False).display_name
        self.assertEqual(display_name, self.product_name,
                         "Code should not be preprended to the name as context should prevent it.")

    def test_default_code_and_negative_operator(self):
        res = self.env['product.template'].name_search(name='PTN', operator='not ilike')
        res_ids = [r[0] for r in res]
        self.assertNotIn(self.product.id, res_ids)

    def test_product_template_search_name_no_product_product(self):
        # To be able to test dynamic variant "variants" feature must be set up
        self.env.user.write({'group_ids': [(4, self.env.ref('product.group_product_variant').id)]})
        color_attr = self.env['product.attribute'].create({'name': 'Color', 'create_variant': 'dynamic'})
        color_attr_value_r = self.env['product.attribute.value'].create({'name': 'Red', 'attribute_id': color_attr.id})
        color_attr_value_b = self.env['product.attribute.value'].create({'name': 'Blue', 'attribute_id': color_attr.id})
        template_dyn = self.env['product.template'].create({
            'name': 'Test Dynamical',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': color_attr.id,
                'value_ids': [(4, color_attr_value_r.id), (4, color_attr_value_b.id)],
            })]
        })
        product = self.env['product.product'].create({
            'name': 'Dynamo Lamp',
            'default_code': 'Dynamo',
        })
        self.assertTrue(template_dyn.has_dynamic_attributes())
        # Ensure that template_dyn hasn't any product_product
        self.assertEqual(len(template_dyn.product_variant_ids), 0)
        # Ensure that Dynam search return Dynamo and Test Dynamical as this
        # last have no product_product
        res = self.env['product.template'].name_search(name='Dynam', operator='ilike')
        res_ids = [r[0] for r in res]
        self.assertIn(template_dyn.id, res_ids)
        self.assertIn(product.product_tmpl_id.id, res_ids)

    def test_product_product_name_search(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Attribute',
            'value_ids': [
                Command.create({'name': f'value {i}'})
                for i in range(3)
            ]
        })
        template = self.env['product.template'].create({
            'name': 'Whatever',
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': attribute.id,
                    'value_ids': [Command.set(attribute.value_ids.ids)]
                })
            ]
        })
        variant1, _variant2, _variant3 = template.product_variant_ids
        variant1.default_code = 'HOHO'
        product_search = self.env['product.product'].with_context(partner_id=33).search([
            ('display_name', '=', 'HOHO'),
        ])
        self.assertEqual(variant1, product_search)

    def test_search_display_name_ilike(self):
    """ilike operator should find product by default_code (cross-table UNION path)."""
    variant = self.env['product.product'].create({
        'name': 'Generic Product',
        'default_code': 'ILIKE_SKU',
    })
    result = self.env['product.product'].search([
        ('display_name', 'ilike', 'ILIKE_SKU'),
    ])
    self.assertIn(variant, result)

def test_search_display_name_in_operator(self):
    """'in' operator should find products matched by name or default_code."""
    v1 = self.env['product.product'].create({'name': 'Alpha'})
    v2 = self.env['product.product'].create({
        'name': 'Unrelated',
        'default_code': 'BETA_CODE',
    })
    result = self.env['product.product'].search([
        ('display_name', 'in', ['Alpha', 'BETA_CODE']),
    ])
    self.assertIn(v1, result)
    self.assertIn(v2, result)

def test_search_display_name_barcode(self):
    """ilike operator should find product matching by barcode."""
    variant = self.env['product.product'].create({
        'name': 'Some Product',
        'barcode': '123456789',
    })
    result = self.env['product.product'].search([
        ('display_name', 'ilike', '123456789'),
    ])
    self.assertIn(variant, result)

def test_search_display_name_supplier_code(self):
    """Supplier product code should be searchable via partner_id context."""
    partner = self.env['res.partner'].create({'name': 'Test Supplier'})
    template = self.env['product.template'].create({'name': 'Supplied Product'})
    self.env['product.supplierinfo'].create({
        'partner_id': partner.id,
        'product_tmpl_id': template.id,
        'product_code': 'SUP_CODE',
    })
    result = self.env['product.product'].with_context(partner_id=partner.id).search([
        ('display_name', 'ilike', 'SUP_CODE'),
    ])
    self.assertIn(template.product_variant_ids[0], result)

def test_search_display_name_negative_operator(self):
    """Negative operator should NOT use UNION path — AND logic must still work."""
    v1 = self.env['product.product'].create({
        'name': 'Exclude Me',
        'default_code': 'EXCL',
    })
    v2 = self.env['product.product'].create({'name': 'Keep Me'})
    result = self.env['product.product'].search([
        ('display_name', 'not ilike', 'Exclude'),
    ])
    self.assertNotIn(v1, result)
    self.assertIn(v2, result)

def test_search_display_name_archived_not_leaked(self):
    """Archived products must not appear in positive operator searches."""
    variant = self.env['product.product'].create({
        'name': 'Archived Product',
        'default_code': 'ARCH_SKU',
        'active': False,
    })
    result = self.env['product.product'].search([
        ('display_name', 'ilike', 'ARCH_SKU'),
    ])
    self.assertNotIn(variant, result)

def test_template_search_display_name_via_variant(self):
    """product.template search should find template matched by variant default_code."""
    template = self.env['product.template'].create({'name': 'Template A'})
    template.product_variant_ids[0].default_code = 'TMPL_SKU'
    result = self.env['product.template'].with_context(
        search_product_product=True
    ).search([
        ('display_name', 'ilike', 'TMPL_SKU'),
    ])
    self.assertIn(template, result)
