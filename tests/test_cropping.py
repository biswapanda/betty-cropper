import os
import shutil

from django.test import TestCase, Client
from django.core.files import File

from betty.conf.app import settings
from betty.cropper.models import Image, Ratio

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'images')


class ImageSavingTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_image_selections(self):
        image = Image.objects.create(
            name="Lenna.gif",
            width=512,
            height=512
        )

        # Test to make sure the default selections work
        self.assertEqual(
            image.get_selection(Ratio('1x1')),
            {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}
        )

        # Now let's add some bad data
        image.selections = {
            '1x1': {
                'x0': 0,
                'y0': 0,
                'x1': 513,
                'y1': 512
            }
        }
        image.save()

        # Now, that was a bad selection, so we should be getting an auto generated one.
        self.assertEqual(
            image.get_selection(Ratio('1x1')),
            {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}
        )

        # Try with a negative value
        image.selections = {
            '1x1': {
                'x0': -1,
                'y0': 0,
                'x1': 512,
                'y1': 512
            }
        }
        image.save()
        self.assertEqual(
            image.get_selection(Ratio('1x1')),
            {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}
        )

        # Try with another negative value
        image.selections = {
            '1x1': {
                'x0': 0,
                'y0': 0,
                'x1': -1,
                'y1': 512
            }
        }
        image.save()
        self.assertEqual(
            image.get_selection(Ratio('1x1')),
            {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}
        )

        # Try with bad x values
        image.selections = {
            '1x1': {
                'x0': 10,
                'y0': 0,
                'x1': 9,
                'y1': 512
            }
        }
        image.save()
        self.assertEqual(
            image.get_selection(Ratio('1x1')),
            {'x0': 0, 'y0': 0, 'x1': 512, 'y1': 512}
        )

    def test_bad_image_id(self):
        res = self.client.get('/images/abc/13x4/256.jpg')
        self.assertEqual(res.status_code, 404)

    def test_bad_ratio(self):
        res = self.client.get('/images/666/13x4/256.jpg')
        self.assertEqual(res.status_code, 404)

    def test_malformed_ratio(self):
        res = self.client.get('/images/666/farts/256.jpg')
        self.assertEqual(res.status_code, 404)

    def test_bad_extension(self):
        res = self.client.get('/images/666/1x1/500.gif')
        self.assertEqual(res.status_code, 404)

    def test_too_large(self):
        res = self.client.get("/images/666/1x1/{}.jpg".format(settings.BETTY_MAX_WIDTH + 1))
        self.assertEqual(res.status_code, 500)

    def test_image_redirect(self):
        res = self.client.get('/images/666666/1x1/100.jpg')
        self.assertRedirects(res, "/images/6666/66/1x1/100.jpg", target_status_code=404)

    def test_placeholder(self):
        settings.BETTY_PLACEHOLDER = True

        res = self.client.get('/images/666/original/256.jpg')
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/images/666/1x1/256.jpg')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'image/jpeg')

        res = self.client.get('/images/666/1x1/256.png')
        self.assertEqual(res['Content-Type'], 'image/png')
        self.assertEqual(res.status_code, 200)

        settings.BETTY_PLACEHOLDER = False
        res = self.client.get('/images/666/1x1/256.jpg')
        self.assertEqual(res.status_code, 404)

    def test_missing_file(self):
        image = Image.objects.create(name="Lenna.gif", width=512, height=512)

        res = self.client.get('/images/{0}/1x1/256.jpg'.format(image.id))
        self.assertEqual(res.status_code, 500)

    def test_image_save(self):

        image = Image.objects.create(
            name="Lenna.png",
            width=512,
            height=512
        )
        lenna = File(open(os.path.join(TEST_DATA_PATH, "Lenna.png"), "rb"))
        image.source.save("Lenna.png", lenna)

        # Now let's test that a JPEG crop will return properly.
        res = self.client.get('/images/{}/1x1/240.jpg'.format(image.id))
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(os.path.exists(os.path.join(image.path(), '1x1', '240.jpg')))

        # Now let's test that a PNG crop will return properly.
        res = self.client.get('/images/{}/1x1/240.png'.format(image.id))
        self.assertEqual(res['Content-Type'], 'image/png')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(os.path.exists(os.path.join(image.path(), '1x1', '240.png')))

        # Let's test an "original" crop
        res = self.client.get('/images/{}/original/240.jpg'.format(image.id))
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(os.path.exists(os.path.join(image.path(), 'original', '240.jpg')))

        # Finally, let's test a width that doesn't exist
        res = self.client.get('/images/{}/original/666.jpg'.format(image.id))
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(os.path.exists(os.path.join(image.path(), 'original', '666.jpg')))

    def test_image_pending(self):
        image = Image.objects.create(
            name="Lenna.png",
            width=512,
            height=512,
            status=Image.PENDING,
            url="http://example.com/lenna/png"
        )

        res = self.client.get('/images/{}/original/666.jpg'.format(image.id))
        self.assertEqual(res.status_code, 202)

    def test_image_failed(self):
        image = Image.objects.create(
            name="Lenna.png",
            width=512,
            height=512,
            status=Image.FAILED,
            url="http://example.com/lenna/png"
        )

        res = self.client.get('/images/{}/original/666.jpg'.format(image.id))
        self.assertEqual(res.status_code, 410)

    def test_non_rgb(self):
        image = Image.objects.create(
            name="animated.gif",
            width=512,
            height=512
        )

        lenna = File(open(os.path.join(TEST_DATA_PATH, "animated.gif"), "rb"))
        image.source.save("animated.gif", lenna)

        res = self.client.get('/images/{}/1x1/240.jpg'.format(image.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertTrue(os.path.exists(os.path.join(image.path(), '1x1/240.jpg')))

        res = self.client.get('/images/{}/original/1200.jpg'.format(image.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'image/jpeg')
        self.assertTrue(os.path.exists(os.path.join(image.path(), 'original/1200.jpg')))

    def test_image_js(self):
        res = self.client.get("/images/image.js")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/javascript')

    def tearDown(self):
        shutil.rmtree(settings.BETTY_IMAGE_ROOT, ignore_errors=True)
