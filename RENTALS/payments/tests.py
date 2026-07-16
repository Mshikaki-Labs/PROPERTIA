from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from invoices.models import InvoicePayment
from leases.models import Lease
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit


class UploadPaymentsTests(TestCase):
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
        Lease.objects.create(
            user=self.user,
            tenant=self.tenant,
            unit=self.unit,
            start_date=date(2026, 1, 1),
            monthly_rent=self.unit.rent_amount,
            is_active=True,
        )

    def make_upload(self, rows, headers=None):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(headers or ['property', 'house number', 'paid in date', 'code', 'details', 'amount'])
        for row in rows:
            sheet.append(row)
        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return SimpleUploadedFile(
            'payments.xlsx',
            stream.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def upload(self, rows, headers=None):
        return self.client.post(reverse('payments:upload_payments'), {'file': self.make_upload(rows, headers)})

    def validate_upload(self, rows, headers=None):
        return self.client.post(reverse('payments:upload_payments'), {
            'file': self.make_upload(rows, headers),
            'validate_only': '1',
        })

    def test_upload_matches_property_and_house_number_to_active_lease_tenant(self):
        response = self.upload([
            ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00'],
        ])

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)

        payment = Payment.objects.get()
        self.assertEqual(payment.property, self.property)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.code, 'RCT')
        self.assertEqual(payment.amount, Decimal('5000.00'))
        self.assertEqual(payment.balance, Decimal('5000.00'))
        self.assertEqual(payment.date, date(2026, 5, 10))
        self.assertEqual(payment.description, 'May rent deposit')
        self.assertEqual(payment.status, 'unclaimed')
        self.assertEqual(InvoicePayment.objects.count(), 0)

    def test_validate_upload_does_not_create_payments(self):
        response = self.validate_upload([
            ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00'],
        ])

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['valid_rows'], 1)
        self.assertEqual(data['invalid_rows'], 0)
        self.assertEqual(Payment.objects.count(), 0)

    def test_upload_accepts_sample_headers_with_house_numner_and_date(self):
        response = self.upload(
            [
                ['Green Court', 'A1', '01-05-2026', 'RCT', '', '8,000.00'],
            ],
            headers=['PROPERTY', 'HOUSE_NUMNER', 'DATE', 'CODE', 'DETAILS', 'AMOUNT'],
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)

        payment = Payment.objects.get()
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.code, 'RCT')
        self.assertEqual(payment.amount, Decimal('8000.00'))
        self.assertEqual(payment.balance, Decimal('8000.00'))
        self.assertEqual(payment.date, date(2026, 5, 1))
        self.assertEqual(payment.description, '')

    def test_payment_list_filters_by_date_range(self):
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('1000.00'),
            date=date(2026, 5, 1),
            description='Before range',
        )
        in_range_payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('2000.00'),
            date=date(2026, 5, 15),
            description='In range',
        )
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('3000.00'),
            date=date(2026, 6, 1),
            description='After range',
        )

        response = self.client.get(reverse('payments:payment_list'), {
            'start_date': '2026-05-10',
            'end_date': '2026-05-20',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, in_range_payment.description)
        self.assertNotContains(response, 'Before range')
        self.assertNotContains(response, 'After range')

    def test_manual_payment_matches_property_and_unit_to_active_lease_tenant(self):
        response = self.client.post(reverse('payments:payment_list'), {
            'property': self.property.id,
            'unit': self.unit.id,
            'code': '2CX',
            'amount': '8000.00',
            'description': '',
            'date': '2026-05-02',
        })

        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get()
        self.assertEqual(payment.property, self.property)
        self.assertEqual(payment.unit, self.unit)
        self.assertEqual(payment.tenant, self.tenant)
        self.assertEqual(payment.code, '2CX')
        self.assertEqual(payment.amount, Decimal('8000.00'))
        self.assertEqual(payment.status, 'unclaimed')

    def test_upload_rejects_unit_without_active_lease(self):
        Lease.objects.update(is_active=False)

        response = self.upload([
            ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00'],
        ])

        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertIn('No active tenant found', data['errors'][0])

    def test_upload_skips_duplicate_payment(self):
        row = ['Green Court', 'A1', '2026-05-10', 'RCT', 'May rent deposit', '5000.00']
        first_response = self.upload([row])
        second_response = self.upload([row])

        self.assertTrue(first_response.json()['success'])
        second_data = second_response.json()
        self.assertFalse(second_data['success'])
        self.assertEqual(second_data['count'], 0)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertIn('Duplicate payment skipped', second_data['errors'][0])
