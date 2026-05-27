from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from invoices.models import Invoice
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit


class InvoiceFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='landlord', password='pass')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Test property',
        )
        self.unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount=Decimal('12000.00'),
            status='occupied',
        )
        self.tenant = Tenant.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000000',
            next_of_kin_phone_number='0711111111',
        )

    def make_invoice(self, amount, due_date):
        return Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal(amount),
            type='Rent',
            due_date=due_date,
        )

    def test_invoice_list_filters_by_due_date_range(self):
        before = self.make_invoice('1000.00', date(2026, 5, 1))
        in_range = self.make_invoice('2000.00', date(2026, 5, 15))
        after = self.make_invoice('3000.00', date(2026, 6, 1))

        response = self.client.get(reverse('invoices:invoice_list'), {
            'start_date': '2026-05-10',
            'end_date': '2026-05-20',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, in_range.invoice_number)
        self.assertNotContains(response, before.invoice_number)
        self.assertNotContains(response, after.invoice_number)

    def test_invoice_list_filters_by_unit(self):
        other_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='B2',
            rent_amount=Decimal('15000.00'),
            status='occupied',
        )
        selected_invoice = self.make_invoice('1000.00', date(2026, 5, 1))
        other_invoice = Invoice.objects.create(
            user=self.user,
            unit=other_unit,
            tenant=self.tenant,
            amount=Decimal('2000.00'),
            type='Rent',
            due_date=date(2026, 5, 2),
        )

        response = self.client.get(reverse('invoices:invoice_list'), {'unit': self.unit.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, selected_invoice.invoice_number)
        self.assertNotContains(response, other_invoice.invoice_number)
