from django.db import models
from django.conf import settings

banner_images_path = "banner/files/"

SITE_DOMAIN = settings.SITE_DOMAIN
MEDIA_PATH = settings.MEDIA_ROOT

class Banner(models.Model):
    name = models.CharField(blank=True, null=True, max_length=255)
    is_active = models.BooleanField(default=True)
    banner_file = models.FileField(upload_to=banner_images_path, null=True, blank=True)


    def __str__(self):
        return self.name

    def get_banner_file(self):
        if self.banner_file:
            return SITE_DOMAIN + self.banner_file.url
        else:
            return ""
