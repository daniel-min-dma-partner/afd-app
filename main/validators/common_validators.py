import re

from django.core.exceptions import ValidationError


def xss_absent_validator(value):
    any_multilined = r'(.|\n| )*'
    validations = [
        (fr'(?=(<script.*?[>]?{any_multilined}[</script>]?))', 'script_html_tag'),
        (fr'(?=(alert\(.*?{any_multilined}[\)]?))', 'alert_js_func')
    ]
    errors = []
    [
        errors.append(ValidationError("Malformed Input value", code=forb_patt[1]))
        for forb_patt in validations if re.findall(forb_patt[0], value, re.MULTILINE)
    ]

    if len(errors):
        raise ValidationError(errors)
