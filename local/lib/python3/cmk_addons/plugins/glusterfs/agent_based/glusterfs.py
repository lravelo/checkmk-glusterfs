#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    Result,
    Service,
    State,
    Metric,
    HostLabel,
)


# ---------------------------
# Agent Section + Host Labels
# ---------------------------
def host_labels_glusterfs(section):
    yield HostLabel("inett/glusterfs", "server")


agent_section_glusterfs = AgentSection(
    name="glusterfs",
    parse_function=lambda x: x,  # keep raw section
    host_label_function=host_labels_glusterfs,
)


# ---------------------------
# PEER DISCOVERY
# ---------------------------
def discover_glusterfs_peer(section):
    first = True
    gluster_found = False
    gluster_section = None

    for line in section:
        line = " ".join(line).split()

        if first:
            first = False
            gluster_found = line[0].startswith("0")

        elif gluster_found and gluster_section == "pool_list":
            if line[0].startswith("#"):
                gluster_section = None
            elif line == ["UUID", "Hostname", "State"]:
                continue
            else:
                for i in range(len(line) - 1):
                    if i % 3 == 1:
                        yield Service(item=line[i])

        if gluster_found and gluster_section is None and line == ["#", "gluster", "pool", "list"]:
            gluster_section = "pool_list"


def check_glusterfs_peer(item, section):
    pool_list_section = False
    peer_status_section = False
    peer_status_host_section = False
    pool_list_dropline = False

    for line in section:
        line = " ".join(line).split()

        if pool_list_section:
            if item in line:
                ind = line.index(item)

                yield Result(state=State.OK, summary=f"UUID: {line[ind - 1]}")
                yield Result(state=State.OK, summary=f"Hostname: {line[ind]}")

                yield Result(
                    state=State.OK if line[ind + 1] == "Connected" else State.CRIT,
                    summary=f"State: {line[ind + 1]}",
                )

            if line[0] == "#":
                pool_list_section = False
                peer_status_section = False

        elif peer_status_section:
            if peer_status_host_section:
                if line[0] == "State:":
                    stateline = " ".join(line[1:])
                    state = stateline.split(" (")

                    if state[0] == "Peer in Cluster":
                        r_state = State.OK
                    elif state[0] == "Accepted Peer Request":
                        r_state = State.WARN
                    elif state[0] == "Peer Rejected":
                        r_state = State.CRIT
                    else:
                        r_state = State.UNKNOWN

                    yield Result(state=r_state, summary=f"{state[0]} ({item})")

            if peer_status_host_section and not " ".join(line).strip():
                peer_status_section = False
                peer_status_host_section = False

            elif line[0] == "Hostname:" and line[1] == item:
                peer_status_host_section = True

        if line == ["#", "gluster", "peer", "status"]:
            peer_status_section = True
        elif line == ["#", "gluster", "pool", "list"]:
            pool_list_section = True
            pool_list_dropline = True


check_plugin_glusterfs_peer = CheckPlugin(
    name="glusterfs_peer",
    sections=["glusterfs"],
    service_name="GlusterFS peer %s",
    discovery_function=discover_glusterfs_peer,
    check_function=check_glusterfs_peer,
)


# ---------------------------
# VOLUME DISCOVERY
# ---------------------------
def discover_glusterfs_volume(section):
    first = True
    gluster_found = False
    gluster_section = None
    skip_first = True

    for line in section:
        line = " ".join(line).split()

        if first:
            first = False
            gluster_found = line[0].startswith("0")

        elif gluster_found and gluster_section == "volume_list":
            if line[0].startswith("#") and not skip_first:
                gluster_section = None
            elif skip_first:
                skip_first = False
            elif line[:2] == ["Volume", "Name:"]:
                yield Service(item=line[2])

        elif gluster_found and gluster_section is None and line == ["#", "gluster", "volume", "list"]:
            gluster_section = "volume_list"


def check_glusterfs_volume(item, section):
    skip = 0
    volume_info_section = False
    volume_heal_info_section = False
    volume_heal_info_sbrain_section = False
    volume_rebalance_status_section = False

    brick = None
    total_h = 0
    total_sb = 0
    total_rebalance = [0, 0, 0, 0, 0]

    for line in section:
        line = " ".join(line).split()

        if not line:
            continue

        if line[0] == "#":
            volume_info_section = False
            volume_heal_info_section = False
            volume_heal_info_sbrain_section = False
            volume_rebalance_status_section = False

        elif skip > 0:
            skip -= 1
            continue

        elif volume_info_section:
            if len(line) >= 2:
                if line[0] == "Status:" and line[1] != "Started":
                    yield Result(state=State.UNKNOWN, summary=f"Status: {line[1]}")
                elif line[0] != "Volume Name:":
                    yield Result(state=State.OK, summary=" ".join(line))

        elif volume_heal_info_section:
            if line[0] == "Brick":
                brick = line[1]

            elif line[0] == "Status:":
                v_line = " ".join(line)
                if "Connected" in v_line:
                    yield Result(state=State.OK, summary=f"{brick}: {v_line}")
                elif "not Connected" in v_line:
                    yield Result(state=State.CRIT, summary=f"{brick}: {v_line}")
                else:
                    yield Result(state=State.UNKNOWN, summary=f"{brick}: {v_line}")

            elif " ".join(line[:3]) == "Number of entries:":
                if line[3] != "-":
                    val = int(line[3])
                    total_h += val
                    if val > 15:
                        yield Result(state=State.CRIT, summary=" ".join(line))
                    elif val > 10:
                        yield Result(state=State.WARN, summary=" ".join(line))
                else:
                    yield Result(state=State.UNKNOWN, summary=" ".join(line))

        elif volume_heal_info_sbrain_section:
            if line[0] == "Brick":
                brick = line[1]

            if " ".join(line[:5]) == "Number of entries in split-brain:":
                if line[5] != "-":
                    val = int(line[5])
                    total_sb += val
                    if val > 1:
                        yield Result(state=State.CRIT, summary=f"{val} split-brain entries")
                else:
                    yield Result(state=State.UNKNOWN, summary="split-brain unknown")

        elif volume_rebalance_status_section:
            if line[0] != "volume" and line[1] != "fix-layout":
                total_rebalance[0] += int(line[1])
                total_rebalance[1] += int(line[2].replace("Bytes", ""))
                total_rebalance[2] += int(line[3])
                total_rebalance[3] += int(line[4])
                total_rebalance[4] += int(line[5])

                yield Result(state=State.OK, summary=f"{line[0]} rebalanced files: {line[1]}")

                time = line[7].split(":")
                seconds = int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2])
                yield Metric(f"{line[0]}_rebalance_time", seconds)

        # Section switches
        if line[0] == "#":
            if line == ["#", "gluster", "volume", "info", item]:
                volume_info_section = True
            elif line == ["#", "gluster", "volume", "heal", item, "info"]:
                volume_heal_info_section = True
            elif line == ["#", "gluster", "volume", "heal", item, "info", "split-brain"]:
                volume_heal_info_sbrain_section = True
            elif line == ["#", "gluster", "volume", "rebalance", item, "status"]:
                volume_rebalance_status_section = True
                skip = 2

    yield Metric("total_num_unhealthy", total_h, levels=(10, 15))
    yield Metric("total_num_sb_error", total_sb, levels=(1, 1))


check_plugin_glusterfs_volume = CheckPlugin(
    name="glusterfs_volume",
    sections=["glusterfs"],
    service_name="GlusterFS volume %s",
    discovery_function=discover_glusterfs_volume,
    check_function=check_glusterfs_volume,
)
