import shutil
import tempfile
from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from invoices.models import Invoice
from payments.forms import PaymentForm
from payments.models import Payment
from properties.models import Property
from units.forms import UnitForm
from units.models import Unit

from .forms import TenantForm
from .models import Tenant


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TenantDocumentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='password12345')
        self.property = Property.objects.create(
            user=self.user,
            name='Test Property',
            address='123 Test Street',
            county='Nairobi',
            total_units=1,
            description='Test property',
        )

    def test_document_fields_are_optional(self):
        form = TenantForm(data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
        }, user=self.user)

        self.assertTrue(form.is_valid(), form.errors)

    def test_add_tenant_accepts_id_card_front_back_and_kra_pin_text(self):
        self.client.login(username='owner', password='password12345')

        response = self.client.post(reverse('tenants:tenant_list'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
            'id_card_front': SimpleUploadedFile('id-card-front.txt', b'id card front'),
            'id_card_back': SimpleUploadedFile('id-card-back.txt', b'id card back'),
            'kra_pin': 'A123456789B',
        })

        self.assertEqual(response.status_code, 302)
        tenant = Tenant.objects.get(first_name='Jane')
        self.assertTrue(tenant.id_card_front.name.startswith('tenant_documents/id_cards/front/'))
        self.assertTrue(tenant.id_card_back.name.startswith('tenant_documents/id_cards/back/'))
        self.assertEqual(tenant.kra_pin, 'A123456789B')

    def test_upload_tenants_accepts_id_card_front_back_and_kra_pin_headers(self):
        self.client.login(username='owner', password='password12345')
        csv_file = SimpleUploadedFile(
            'tenants.csv',
            (
                'first_name,last_name,phone_number,property,id_card_front,id_card_back,kra_pin,next_of_kin_phone_number\n'
                'Jane,Doe,0712345678,Test Property,id-front.pdf,id-back.pdf,A123456789B,0798765432\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = self.client.post(reverse('tenants:upload_tenants'), {'file': csv_file})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        tenant = Tenant.objects.get(first_name='Jane')
        self.assertEqual(tenant.id_card_front.name, 'id-front.pdf')
        self.assertEqual(tenant.id_card_back.name, 'id-back.pdf')
        self.assertEqual(tenant.kra_pin, 'A123456789B')


class ScopedFormQuerysetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='scoped-form-owner', password='pass12345')
        self.own_property = Property.objects.create(
            user=self.user,
            name='Owned Property',
            address='1 Owned Road',
            county='Nairobi',
            total_units=1,
            description='Owned property',
        )
        self.own_unit = Unit.objects.create(
            user=self.user,
            property=self.own_property,
            name='B1',
            rent_amount='3000.00',
            description='Owned unit',
        )
        self.other_user = User.objects.create_user(username='other-form-owner', password='pass12345')
        self.other_property = Property.objects.create(
            user=self.other_user,
            name='Other Property',
            address='2 Other Road',
            county='Nairobi',
            total_units=1,
            description='Other property',
        )
        self.other_unit = Unit.objects.create(
            user=self.other_user,
            property=self.other_property,
            name='C1',
            rent_amount='4000.00',
            description='Other unit',
        )

    def test_tenant_form_only_lists_owned_properties(self):
        form = TenantForm(user=self.user)

        self.assertEqual(list(form.fields['property'].queryset), [self.own_property])

    def test_unit_form_only_lists_owned_properties(self):
        form = UnitForm(user=self.user)

        self.assertEqual(list(form.fields['property'].queryset), [self.own_property])

    def test_payment_form_only_lists_owned_properties_and_units(self):
        form = PaymentForm(user=self.user)

        self.assertEqual(list(form.fields['property'].queryset), [self.own_property])
        self.assertEqual(list(form.fields['unit'].queryset), [self.own_unit])


class TenantPaginationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tenant-paginate', password='pass12345')
        self.client.force_login(self.user)

    def test_tenants_page_shows_pagination_controls(self):
        for index in range(15):
            Tenant.objects.create(
                first_name=f'User{index}',
                last_name='Example',
                phone_number=f'07000000{index}',
                next_of_kin_phone_number=f'07111111{index}',
            )

        response = self.client.get(reverse('tenants:tenant_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rows')
        self.assertContains(response, 'per_page')


class TenantLedgerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ledger-owner', password='pass12345')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='123 Main',
            county='Nairobi',
            total_units=1,
            description='Ledger property',
        )
        self.unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount='5000.00',
            description='Test unit',
        )
        self.same_property_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A2',
            rent_amount='6000.00',
            description='Same property unit',
        )
        self.tenant = Tenant.objects.create(
            first_name='Jane',
            last_name='Doe',
            phone_number='0712345678',
            next_of_kin_phone_number='0798765432',
            unit=self.unit,
            status='active',
        )
        self.same_property_tenant = Tenant.objects.create(
            first_name='John',
            last_name='Neighbor',
            phone_number='0712345679',
            next_of_kin_phone_number='0798765433',
            unit=self.same_property_unit,
            status='active',
        )
        self.other_property = Property.objects.create(
            user=self.user,
            name='Blue Court',
            address='456 Side',
            county='Nairobi',
            total_units=1,
            description='Other ledger property',
        )
        self.other_property_unit = Unit.objects.create(
            user=self.user,
            property=self.other_property,
            name='B1',
            rent_amount='7000.00',
            description='Other property unit',
        )
        self.other_property_tenant = Tenant.objects.create(
            first_name='Mary',
            last_name='Elsewhere',
            phone_number='0712345680',
            next_of_kin_phone_number='0798765434',
            unit=self.other_property_unit,
            status='active',
        )
        self.other_user = User.objects.create_user(username='ledger-other-owner', password='pass12345')
        self.unowned_property = Property.objects.create(
            user=self.other_user,
            name='Hidden Court',
            address='789 Away',
            county='Nairobi',
            total_units=1,
            description='Unowned ledger property',
        )
        self.unowned_unit = Unit.objects.create(
            user=self.other_user,
            property=self.unowned_property,
            name='C1',
            rent_amount='8000.00',
            description='Unowned unit',
        )
        self.unowned_tenant = Tenant.objects.create(
            first_name='Una',
            last_name='Hidden',
            phone_number='0712345681',
            next_of_kin_phone_number='0798765435',
            unit=self.unowned_unit,
            status='active',
        )
        self.invoice = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount='5000.00',
            due_date=date(2026, 7, 1),
            status='Unpaid',
        )
        self.payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            code='RCT-2500',
            amount='2500.00',
            balance='2500.00',
            description='Partial rent payment',
            date=date(2026, 7, 2),
            status='claimed',
        )

    def test_ledger_page_displays_invoice_and_payment_entries(self):
        response = self.client.get(reverse('tenants:tenant_ledger', args=[self.tenant.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tenant Ledger')
        self.assertContains(response, '<th>Code</th>', html=True)
        self.assertContains(response, 'RCT-2500')
        self.assertContains(response, 'Partial rent payment')
        self.assertContains(response, 'INV-')

    def test_ledger_tenant_switcher_only_lists_tenants_from_same_owned_property(self):
        response = self.client.get(reverse('tenants:tenant_ledger', args=[self.tenant.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change Tenant')
        self.assertContains(response, 'Jane Doe - A1')
        self.assertContains(response, 'John Neighbor - A2')
        self.assertNotContains(response, 'Mary Elsewhere - B1')
        self.assertNotContains(response, 'Una Hidden - C1')

    def test_ledger_blocks_tenants_from_other_users(self):
        response = self.client.get(reverse('tenants:tenant_ledger', args=[self.unowned_tenant.id]))

        self.assertEqual(response.status_code, 404)


class TenantListCleanupTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cleanup-owner', password='pass12345')
        self.client.force_login(self.user)
        self.own_property = Property.objects.create(
            user=self.user,
            name='Own Property',
            address='1 Own Road',
            county='Nairobi',
            total_units=1,
            description='Owned property',
        )
        self.own_unit = Unit.objects.create(
            user=self.user,
            property=self.own_property,
            name='B1',
            rent_amount='3000.00',
            description='Owned unit',
        )
        self.other_user = User.objects.create_user(username='other-owner', password='pass12345')
        self.other_property = Property.objects.create(
            user=self.other_user,
            name='Other Property',
            address='2 Other Road',
            county='Nairobi',
            total_units=1,
            description='Other property',
        )
        self.other_unit = Unit.objects.create(
            user=self.other_user,
            property=self.other_property,
            name='C1',
            rent_amount='4000.00',
            description='Other unit',
        )

    def test_tenant_list_removes_orphans_and_limits_filters_to_owned_properties(self):
        Tenant.objects.create(
            first_name='Orphan',
            last_name='Tenant',
            phone_number='0710000000',
            next_of_kin_phone_number='0790000000',
        )
        Tenant.objects.create(
            first_name='Owned',
            last_name='Tenant',
            phone_number='0710000001',
            next_of_kin_phone_number='0790000001',
            unit=self.own_unit,
        )
        Tenant.objects.create(
            first_name='Other',
            last_name='Tenant',
            phone_number='0710000002',
            next_of_kin_phone_number='0790000002',
            unit=self.other_unit,
        )

        response = self.client.get(reverse('tenants:tenant_list'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tenant.objects.filter(first_name='Orphan').exists())
        self.assertTrue(Tenant.objects.filter(first_name='Owned').exists())
        self.assertTrue(Tenant.objects.filter(first_name='Other').exists())
        self.assertContains(response, 'Owned Tenant')
        self.assertNotContains(response, 'Orphan Tenant')
        self.assertNotContains(response, 'Other Tenant')
        self.assertEqual(list(response.context['properties']), [self.own_property])

    def test_add_tenant_form_only_lists_owned_properties(self):
        response = self.client.get(reverse('tenants:tenant_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['form'].fields['property'].queryset),
            [self.own_property],
        )

    def test_add_tenant_rejects_unowned_property(self):
        response = self.client.post(reverse('tenants:tenant_list'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.other_property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'deposit_amount': '0.00',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('property', response.context['form'].errors)
        self.assertFalse(Tenant.objects.filter(first_name='Jane', last_name='Doe').exists())

    def test_available_units_requires_owned_property(self):
        own_response = self.client.get(reverse('tenants:available_units', args=[self.own_property.id]))
        other_response = self.client.get(reverse('tenants:available_units', args=[self.other_property.id]))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(own_response.json()['units'][0]['id'], self.own_unit.id)
        self.assertEqual(other_response.status_code, 404)
