#!/usr/bin/env python3

from cmk.rulesets.v1 import Title, Label
from cmk.rulesets.v1.rule_specs import AgentConfig
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    BooleanChoice,
)

from cmk.base.cee.plugins.bakery import BakeryPlugin
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Bakery Rule (WATO UI)
# ---------------------------------------------------------------------------

def _agent_config_form():
    return Dictionary(
        title=Title("GlusterFS agent deployment"),
        elements={
            "deploy_plugin": DictElement(
                parameter_form=BooleanChoice(
                    title=Title("Deploy GlusterFS agent plugin"),
                    label=Label("Install the glusterfs agent plugin on the host"),
                ),
                required=False,
                default_value=True,
            ),
        },
    )


rule_spec_glusterfs_agent = AgentConfig(
    name="glusterfs",
    title=Title("GlusterFS agent deployment"),
    parameter_form=_agent_config_form,
)


# ---------------------------------------------------------------------------
# Bakery File Deployment Logic
# ---------------------------------------------------------------------------

def get_glusterfs_files(conf) -> List[Tuple[str, str, int]]:
    """
    Returns files to be included in the baked agent.
    (source, target, permissions)
    """
    files: List[Tuple[str, str, int]] = []

    # Default behavior: deploy plugin unless explicitly disabled
    if conf.get("deploy_plugin", True):
        files.append((
            "libexec/agent_glusterfs",      # source inside MKP
            "plugins/agent_glusterfs",      # destination on host
            0o755,                         # executable
        ))

    return files


# ---------------------------------------------------------------------------
# Bakery Plugin Registration
# ---------------------------------------------------------------------------

bakery_plugin_glusterfs = BakeryPlugin(
    name="glusterfs",
    files_function=get_glusterfs_files,
)