#!/usr/bin/python3
#-*- coding: utf-8 -*-

import default_config

def merge(default, custom):
    r = {}
    for k, v in default.items():
        r[k] = v if k not in custom else custom[k]
    return r

try:
    import custom_config

    default_configs = default_config.configs
    custom_configs = custom_config.configs

    configs = merge(default_configs, custom_configs)

except ImportError:
    pass

