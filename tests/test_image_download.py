import os
import shutil

from django.test import TestCase, Client

from betty.conf.app import settings
from betty.cropper.models import Image

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class ImageDownloadTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_image_create(self):
        image = Image.objects.create_from_url("http://example.com/test_image.png")
        assert image.status == Image.PENDING

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)
