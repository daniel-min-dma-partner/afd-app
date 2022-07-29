import re

from django.core.exceptions import ValidationError


def xss_absent_validator(value):
    any_multilined = r'(.|\n| )*'
    no_xss_validation = [
        (fr'(?=(<script.*?[>]?{any_multilined}[</script>]?))', 'script_html_tag'),
        (fr'(?=(alert\(.*?{any_multilined}[\)]?))', 'alert_js_func')
    ]
    errors = []

    if any([re.findall(forb_patt[0], value, re.MULTILINE) for forb_patt in no_xss_validation]):
        raise ValidationError("Malformed Input Value")
