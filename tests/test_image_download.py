import os
import pytest
import shutil

from django.core.exceptions import ValidationError
from django.test import TestCase, Client

from betty.conf.app import settings
from betty.cropper.models import Image

from httmock import urlmatch, HTTMock, response

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


@urlmatch(netloc=r"(.*\.)?example\.com$", path=r"/lenna\.png")
def lenna(url, request):
    path = os.path.join(TEST_DATA_PATH, "Lenna.png")
    lenna = open(path, "r")
    return response(200, lenna.read(), {"content-type": "image/png"}, None, 5, request)


@urlmatch(netloc=r"(.*\.)?example\.com$", path=r"/404\.png")
def nothing(url, request):
    return response(404, "Nothing here!", {"content-type": "text/html"}, None, 5, request)

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class ImageDownloadTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_image_create(self):
        with HTTMock(lenna):
            image = Image.objects.create_from_url("http://example.com/lenna.png")

        assert image.status == Image.PENDING

        # Let's reload to get the doanload status
        image = Image.objects.get(id=image.id)
        assert image.status == Image.DONE
        assert image.width == 512
        assert image.height == 512
        self.assertTrue(os.path.exists(image.optimized.path))
        self.assertTrue(os.path.exists(image.source.path))

    def test_bad_url(self):
        with pytest.raises(ValidationError):
            Image.objects.create_from_url("/lenna.png")

        with pytest.raises(ValidationError):
            Image.objects.create_from_url("ssh://lenna.png")

    def test_404(self):
        with HTTMock(lenna):
            image = Image.objects.create_from_url("http://example.com/404.png")

        assert image.status == Image.PENDING
        # Let's reload to get the doanload status
        image = Image.objects.get(id=image.id)
        assert image.status == Image.FAILED

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)
