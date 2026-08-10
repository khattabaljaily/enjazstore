from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase


class PwaTemplateTests(TestCase):
    def test_service_worker_registration_is_absent_for_local_templates(self):
        request = RequestFactory().get('/', HTTP_HOST='localhost:8000')
        request.session = self.client.session
        request.user = type('UserStub', (), {'is_authenticated': False})()
        html = render_to_string('base.html', {'request': request}, request=request)

        self.assertNotIn('serviceWorker', html)
        self.assertNotIn('navigator.serviceWorker.register', html)
