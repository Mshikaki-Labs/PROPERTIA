from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from arrears.models import Arrears
from invoices.models import Invoice
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit


class ArrearsReportTests(TestCase):
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

    def make_invoice(self, status='Unpaid'):
        return Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('12000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=10),
            status=status,
        )

    def test_report_creates_and_shows_arrears_for_overdue_invoice(self):
        invoice = self.make_invoice()

        response = self.client.get(reverse('arrears:arrears_report'))

        self.assertEqual(response.status_code, 200)
        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.amount_due, Decimal('12000.00'))
        self.assertEqual(arrears.days_overdue, 10)
        self.assertContains(response, invoice.invoice_number)
        self.assertContains(response, 'Jane Doe')

    def test_report_uses_remaining_invoice_balance(self):
        invoice = self.make_invoice(status='Partially Paid')
        payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            balance=Decimal('0.00'),
            date=date.today(),
            status='claimed',
        )
        invoice.invoice_payments.create(payment=payment, amount_applied=Decimal('5000.00'))

        self.client.get(reverse('arrears:arrears_report'))

        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.amount_due, Decimal('7000.00'))

    def test_report_resolves_arrears_when_invoice_is_paid(self):
        invoice = self.make_invoice()
        self.client.get(reverse('arrears:arrears_report'))
        invoice.status = 'Paid'
        invoice.save()

        self.client.get(reverse('arrears:arrears_report'))

        arrears = Arrears.objects.get(invoice=invoice)
        self.assertEqual(arrears.status, 'resolved')
        self.assertIsNotNone(arrears.date_resolved)
