import gzip
import io
import json
import zlib

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.text import compress_string


# Source: https://gist.github.com/tomfa/665f8a655a9218e0b4e9bd394d459934
# Customized.
class CompressedBinaryField(models.BinaryField):
    compress = compress_string

    @staticmethod
    def uncompress(s):
        zbuf = io.BytesIO(s)
        zfile = gzip.GzipFile(fileobj=zbuf)
        ret = zfile.read()
        zfile.close()
        return ret

    def get_db_prep_save(self, value, connection=None, prepared=False):
        if value is not None and prepared is False:
            value = zlib.compress(value, 9)
        return models.BinaryField.get_db_prep_save(self, value, connection)

    def is_binary(self, value):
        return value and (type(value) == bytes or isinstance(value, memoryview))

    def _get_val_from_obj(self, obj):
        val = obj and getattr(obj, self.attname)
        if self.is_binary(val):
            return zlib.decompress(val)
        if val is None:
            return self.get_default()
        return val

    def post_init(self, instance=None, **kwargs):
        value = self._get_val_from_obj(instance)
        setattr(instance, self.attname, value)

    def contribute_to_class(self, cls, name, private_only=False):
        super(CompressedBinaryField, self).contribute_to_class(cls, name)
        models.signals.post_init.connect(self.post_init, sender=cls)

    def get_internal_type(self):
        return 'BinaryField'


class CompressedJSONField(CompressedBinaryField):
    encoder = DjangoJSONEncoder

    def __init__(self, *args, **kwargs):
        self.encoder = self.__class__.encoder
        super().__init__(*args, **kwargs)

    def get_db_prep_save(self, value, connection=None, prepared=False):
        if value is not None and prepared is False:
            value = json.dumps(value, cls=self.encoder).encode('utf-8')
        return super().get_db_prep_save(value, connection, prepared)

    def _get_val_from_obj(self, obj):
        if obj:
            val = super()._get_val_from_obj(obj)
            if self.is_binary(val):
                return json.loads(val.decode('utf-8'))
            return val
        else:
            return self.get_default()
