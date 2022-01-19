import re

from django.core.exceptions import ValidationError


def xss_absent_validator(value):
    any_multilined = r'(.|\n| )*'
    script_tag = fr'(?=(<script.*?>{any_multilined}</script>))'
    if re.findall(script_tag, value, re.MULTILINE):
        print('error with', value)
        raise ValidationError("Malformed input detected")
