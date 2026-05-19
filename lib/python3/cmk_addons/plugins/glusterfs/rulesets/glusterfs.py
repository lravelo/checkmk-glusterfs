#!/usr/bin/env python3

from cmk.rulesets.v1 import Title, Help, Topic, ruleset_registry
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    Integer,
)
from cmk.rulesets.v1.rule_specs import (
    CheckParameters,
)


# ---------------------------
# GlusterFS Volume Rules
# ---------------------------

def _valuespec_glusterfs_volume():
    return Dictionary(
        title=Title("GlusterFS volume thresholds"),
        help_text=Help("Configure thresholds for GlusterFS volumes."),
        elements={
            "heal_warn": Integer(
                title=Title("Warning at number of heal entries"),
                default_value=10,
            ),
            "heal_crit": Integer(
                title=Title("Critical at number of heal entries"),
                default_value=15,
            ),
            "splitbrain_crit": Integer(
                title=Title("Critical at split-brain entries"),
                default_value=1,
            ),
        },
    )


ruleset_registry.register(
    CheckParameters(
        name="glusterfs_volume",
        title=Title("GlusterFS volume"),
        topic=Topic.APPLICATIONS,
        parameter_form=_valuespec_glusterfs_volume,
    )
)


# ---------------------------
# GlusterFS Peer Rules
# ---------------------------

def _valuespec_glusterfs_peer():
    return Dictionary(
        title=Title("GlusterFS peer state"),
        help_text=Help("Define how peer states are evaluated."),
        elements={
            "peer_warn": Integer(
                title=Title("Warning if peer not in cluster"),
                default_value=1,
            ),
        },
    )


ruleset_registry.register(
    CheckParameters(
        name="glusterfs_peer",
        title=Title("GlusterFS peer"),
        topic=Topic.APPLICATIONS,
        parameter_form=_valuespec_glusterfs_peer,
    )
)
