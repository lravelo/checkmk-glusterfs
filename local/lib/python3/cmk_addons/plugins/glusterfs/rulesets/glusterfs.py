#!/usr/bin/env python3

from cmk.rulesets.v1 import Title, Label
from cmk.rulesets.v1.rule_specs import CheckParameters, HostCondition
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    Integer,
    BooleanChoice,
)


# ---------------------------------------------------------------------------
# Parameter Form
# ---------------------------------------------------------------------------

def _parameter_form():
    return Dictionary(
        title=Title("GlusterFS monitoring parameters"),
        elements={

            "brick_down_warn": DictElement(
                parameter_form=Integer(
                    title=Title("Warning if this many bricks are down"),
                    help=(
                        "Number of bricks that must be down before the service "
                        "changes to WARNING."
                    ),
                ),
                required=False,
            ),

            "brick_down_crit": DictElement(
                parameter_form=Integer(
                    title=Title("Critical if this many bricks are down"),
                    help=(
                        "Number of bricks that must be down before the service "
                        "changes to CRITICAL."
                    ),
                ),
                required=False,
            ),

            "warn_on_heal": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Warn if self-heal is in progress"),
                    label=Label("Enable warning when heal activity is detected"),
                ),
                required=False,
            ),
        },
    )


# ---------------------------------------------------------------------------
# Ruleset Registration
# ---------------------------------------------------------------------------

rule_spec_glusterfs = CheckParameters(
    name="glusterfs",
    title=Title("GlusterFS"),
    topic="storage",              # ✅ STRING instead of Topic enum
    condition=HostCondition(),   # ✅ REQUIRED
    parameter_form=_parameter_form,
)