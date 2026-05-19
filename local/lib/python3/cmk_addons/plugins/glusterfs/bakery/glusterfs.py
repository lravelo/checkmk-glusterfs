#!/usr/bin/env python3

from cmk.base.plugins.bakery.bakery_api.v1 import (
    Plugin,
    register,
)


def bake_glusterfs_plugin(conf):
    # conf contains parameters from your ruleset
    yield Plugin(
        name="glusterfs",
        source="agents/plugins/glusterfs",
    )


register.bakery_plugin(
    name="glusterfs",
    files_function=bake_glusterfs_plugin,
)
