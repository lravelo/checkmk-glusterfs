#!/usr/bin/env python3

from cmk.rulesets.v1 import Title, Label
from cmk.rulesets.v1.rule_specs import CheckParameters
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    Integer,
    BooleanChoice,
    DefaultValue,
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
                        "Set the number of bricks that must be down before the "
                        "service goes into WARNING state."
                    ),
                ),
                required=False,
                default_value=1,
            ),

            "brick_down_crit": DictElement(
                parameter_form=Integer(
                    title=Title("Critical if this many bricks are down"),
                    help=(
                        "Set the number of bricks that must be down before the "
                        "service goes into CRITICAL state."
                    ),
                ),
                required=False,
                default_value=1,
            ),

            "warn_on_heal": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Warn if self-heal is in progress"),
                    label=Label("Enable warning when heal operations are detected"),
                ),
                required=False,
                default_value=True,
            ),
        },
    )


# ---------------------------------------------------------------------------
# Ruleset Registration
# ---------------------------------------------------------------------------

rule_spec_glusterfs = CheckParameters(
    name="glusterfs",
    title=Title("GlusterFS"),
    parameter_form=_parameter_form,
)
