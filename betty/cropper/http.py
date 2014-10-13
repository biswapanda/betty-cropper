import io
import random

from django.http import HttpResponse

from PIL import Image, ImageDraw, ImageFont

from betty.cropper.models import Ratio
from betty.conf.app import settings


EXTENSION_MAP = {
    "jpg": {
        "format": "jpeg",
        "mime_type": "image/jpeg"
    },
    "png": {
        "format": "png",
        "mime_type": "image/png"
    },
}


class PlaceholderResponse(HttpResponse):

    def __init__(self, ratio, width, extension, *args, **kwargs):
        super(PlaceholderResponse, self).__init__(*args, **kwargs)
        self.status_code = 200

        if ratio.string == "original":
            ratio = Ratio(random.choice((settings.BETTY_RATIOS)))
        height = int(round((width * ratio.height / float(ratio.width))))

        bg_fill = random.choice(settings.BETTY_PLACEHOLDER_COLORS)
        img = Image.new("RGB", (width, height), bg_fill)

        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(filename=settings.BETTY_PLACEHOLDER_FONT, size=45)
        text_size = draw.textsize(ratio.string, font=font)
        text_coords = (
            int(round((width - text_size[0]) / 2.0)),
            int(round((height - text_size[1]) / 2) - 15),
        )
        draw.text(text_coords, ratio.string, font=font, fill=(256, 256, 256))

        if extension == "jpg":
            self._container = [img.tobytes("jpeg", "RGB")]
        if extension == "png":
            # I apparently can't get an encoder for this
            tmp = io.BytesIO()
            img.save(tmp, format="png")
            self._container = [tmp.getvalue()]

        self["Cache-Control"] = "no-cache, no-store, must-revalidate"
        self["Pragma"] = "no-cache"
        self["Expires"] = "0"
        self["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]


class PendingResponse(HttpResponse):
    def __init__(self, ratio, width, extension, *args, **kwargs):
        super(PendingResponse, self).__init__(*args, **kwargs)
        self.status_code = 202

        if ratio.string == "original":
            ratio = Ratio(settings.BETTY_RATIOS[0])
        height = int(round((width * ratio.height / float(ratio.width))))

        bg_fill = (211, 211, 211)
        img = Image.new("RGB", (width, height), bg_fill)

        if extension == "jpg":
            self._container = [img.tobytes("jpeg", "RGB")]
        if extension == "png":
            # I apparently can't get an encoder for this
            tmp = io.BytesIO()
            img.save(tmp, format="png")
            self._container = [tmp.getvalue()]

        self["Cache-Control"] = "no-cache, no-store, must-revalidate"
        self["Pragma"] = "no-cache"
        self["Expires"] = "0"
        self["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]


class FailureResponse(HttpResponse):
    def __init__(self, ratio, width, extension, *args, **kwargs):
        super(FailureResponse, self).__init__(*args, **kwargs)
        self.status_code = 410

        if ratio.string == "original":
            ratio = Ratio(settings.BETTY_RATIOS[0])
        height = int(round((width * ratio.height / float(ratio.width))))

        bg_fill = (166, 18, 18)
        img = Image.new("RGB", (width, height), bg_fill)

        if extension == "jpg":
            self._container = [img.tobytes("jpeg", "RGB")]
        if extension == "png":
            # I apparently can't get an encoder for this
            tmp = io.BytesIO()
            img.save(tmp, format="png")
            self._container = [tmp.getvalue()]

        self["Content-Type"] = EXTENSION_MAP[extension]["mime_type"]
