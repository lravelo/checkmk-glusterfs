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
    """
    Parses the agent output into structured sections.

    Expected format:
        <<<glusterfs:sep(0)>>>
        [peers]
        ...
        [volume]
        ...
        [status]
        ...
        [heal]
        ...
        [df]
        ...
    """
    section: Dict[str, List[str]] = {}
    current_section: Optional[str] = None

    for row in string_table:
        if not row:
            continue

        line = row[0].strip()

        # Detect section headers like [peers]
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
    """
    Discover services:
    - One cluster service (no item)
    - One service per volume
    """

    # Always create cluster-level service
    yield Service()

    # Discover volumes
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

def check_glusterfs(section: Dict[str, List[str]], item: Optional[str]):
    """
    Evaluate cluster OR volume.
    """

    # ------------------------
    # CLUSTER CHECK (no item)
    # ------------------------
    if item is None:
        peer_lines = section.get("peers", [])

        if not peer_lines:
            yield Result(state=State.UNKNOWN, summary="No peer data available")
            return

        disconnected = False

        for line in peer_lines:
            if "Disconnected" in line:
                disconnected = True
                break

        if disconnected:
            yield Result(state=State.CRIT, summary="One or more peers disconnected")
        else:
            yield Result(state=State.OK, summary="All peers connected")

        return


    # ------------------------
    # VOLUME CHECK (item-based)
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

        # Typical lines contain Y/N for brick status
        if "N" in line:
            down_bricks += 1

        if "Y" in line or "N" in line:
            total_bricks += 1


    # Heal detection (very basic)
    healing = False
    for line in heal_lines:
        if item in line and ("entries" in line or "pending" in line):
            if any(x.isdigit() for x in line):
                healing = True
                break


    # Determine state
    if down_bricks > 0:
        yield Result(
            state=State.CRIT,
            summary=f"{down_bricks}/{total_bricks} bricks down",
        )
        return

    if healing:
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
)
