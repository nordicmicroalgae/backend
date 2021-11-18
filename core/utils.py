import re


def transform_keys(input_dict):
    return {
       re.sub(r'[^a-z0-9]', '_', key.lower()): value
       for key, value in input_dict.items()
    }

def make_attribute_list(input_dict):
    return [
        {'name': key, 'value': value}
        for key, value in input_dict.items()
    ]
