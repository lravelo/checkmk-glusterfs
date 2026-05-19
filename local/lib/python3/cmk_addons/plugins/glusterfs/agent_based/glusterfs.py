#!/usr/bin/env python3

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    Service,
    Result,
    State,
)

from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_glusterfs(string_table: List[List[str]]) -> Dict[str, List[str]]:
    section: Dict[str, List[str]] = {}
    current_section: Optional[str] = None

    for row in string_table:
        if not row:
            continue

        line = row[0].strip()

        if line.startswith("[") and line.endswith("]"):
            current_section = line.strip("[]")
            section[current_section] = []
            continue

        if current_section:
            section[current_section].append(line)

    return section


# ---------------------------------------------------------------------------
# Agent Section
# ---------------------------------------------------------------------------

agent_section_glusterfs = AgentSection(
    name="glusterfs",
    parse_function=parse_glusterfs,
)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_glusterfs(section: Dict[str, List[str]]):
    yield Service()

    volumes = set()

    for line in section.get("volume", []):
        if line.startswith("Volume Name:"):
            volname = line.split(":", 1)[1].strip()
            volumes.add(volname)

    for vol in volumes:
        yield Service(item=vol)


# ---------------------------------------------------------------------------
# Check Logic
# ---------------------------------------------------------------------------

def check_glusterfs(params, section: Dict[str, List[str]], item: Optional[str]):
    warn_bricks = params.get("brick_down_warn", 1)
    crit_bricks = params.get("brick_down_crit", 1)
    heal_warn_enabled = params.get("warn_on_heal", True)

    # ------------------------
    # CLUSTER CHECK
    # ------------------------
    if item is None:
        peer_lines = section.get("peers", [])

        if not peer_lines:
            yield Result(state=State.UNKNOWN, summary="No peer data available")
            return

        for line in peer_lines:
            if "Disconnected" in line:
                yield Result(state=State.CRIT, summary="Peer disconnected")
                return

        yield Result(state=State.OK, summary="All peers connected")
        return


    # ------------------------
    # VOLUME CHECK
    # ------------------------
    status_lines = section.get("status", [])
    heal_lines = section.get("heal", [])

    if not status_lines:
        yield Result(state=State.UNKNOWN, summary="No volume status data")
        return

    down_bricks = 0
    total_bricks = 0

    for line in status_lines:
        if item not in line:
            continue

        if "N" in line:
            down_bricks += 1

        if "Y" in line or "N" in line:
            total_bricks += 1


    # Heal detection
    healing = False
    for line in heal_lines:
        if item in line and any(x.isdigit() for x in line):
            healing = True
            break


    # Threshold logic
    if down_bricks >= crit_bricks:
        yield Result(
            state=State.CRIT,
            summary=f"{down_bricks}/{total_bricks} bricks down (CRIT)",
        )
        return

    if down_bricks >= warn_bricks:
        yield Result(
            state=State.WARN,
            summary=f"{down_bricks}/{total_bricks} bricks down (WARN)",
        )
        return

    if healing and heal_warn_enabled:
        yield Result(
            state=State.WARN,
            summary="Self-heal in progress",
        )
        return

    yield Result(
        state=State.OK,
        summary="Volume healthy",
    )


# ---------------------------------------------------------------------------
# Check Plugin
# ---------------------------------------------------------------------------

check_plugin_glusterfs = CheckPlugin(
    name="glusterfs",
    service_name="GlusterFS %s",
    discovery_function=discover_glusterfs,
    check_function=check_glusterfs,
    check_default_parameters={
        "brick_down_warn": 1,
        "brick_down_crit": 1,
        "warn_on_heal": True,
    },
)
