import re


def transform_keys(input_dict):
    return {
       re.sub(r'[^a-z0-9]', '_', key.lower()): value
       for key, value in input_dict.items()
    }
