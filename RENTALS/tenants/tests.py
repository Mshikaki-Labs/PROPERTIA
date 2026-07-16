import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from properties.models import Property

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
