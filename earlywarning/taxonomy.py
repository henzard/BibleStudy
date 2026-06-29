#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prophecy-node taxonomy and research-domain mapping.

This centralises the node IDs, scripture anchors, and domain groupings that
were previously scattered as string literals across the fetch scripts and the
fig-tree analyser. Keeping it in one place lets every stage agree on labels.

Interpretation policy (unchanged from the project's guardrails):
* Bible-only framing.
* These nodes describe *patterns that resemble* the scriptural descriptions.
* High intensity never means "prophecy fulfilled" or a date — see scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str
    scripture: str
    weight: float  # contribution to overall "beginning of sorrows" strength


# Canonical prophecy nodes referenced across the codebase.
NODES: Dict[str, Node] = {
    "J0": Node("J0", "Beginning of Sorrows", "Matt 24:6-8", 0.30),
    "J3": Node("J3", "Abomination of Desolation", "Dan 9:27; Matt 24:15", 0.08),
    "J4": Node("J4", "Great Tribulation", "Matt 24:21-22", 0.05),
    "J6": Node("J6", "Cosmic Signs", "Matt 24:29; Luke 21:25", 0.10),
    "J7": Node("J7", "Son of Man Appears", "Matt 24:30-31", 0.02),
    "H0": Node("H0", "Babylon / Economic", "Rev 17-18", 0.15),
    "B1": Node("B1", "Beast from the Sea", "Rev 13:1-10", 0.05),
    "B2": Node("B2", "Commerce Control / Mark", "Rev 13:11-18", 0.10),
    "MS0": Node("MS0", "Man of Sin", "2 Thess 2:3-4", 0.05),
    "MS1": Node("MS1", "Lying Signs & Wonders", "2 Thess 2:9-12", 0.03),
    "AC0": Node("AC0", "Antichrist Spirit", "1 John 2:18, 2:22, 4:3", 0.02),
}


@dataclass(frozen=True)
class Domain:
    """A research specialism. Each maps to one or more nodes and the
    collectors that feed it."""

    key: str
    title: str
    node_ids: List[str]
    collectors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


# Specialist research domains. The "Coordinator -> specialist researchers"
# fan-out (war / financial / disaster / ...) is defined here.
DOMAINS: Dict[str, Domain] = {
    "war": Domain(
        "war", "Wars & Conflict", ["J0"],
        collectors=["conflicts", "un_peacekeeping"],
        keywords=["war", "conflict", "offensive", "casualties", "strike",
                  "missile", "invasion", "ceasefire", "displaced"],
    ),
    "disaster": Domain(
        "disaster", "Earthquakes & Disasters", ["J0"],
        collectors=["earthquakes", "disasters"],
        keywords=["earthquake", "magnitude", "flood", "cyclone", "volcano",
                  "drought", "tsunami", "wildfire"],
    ),
    "famine": Domain(
        "famine", "Famine & Humanitarian", ["J0"],
        collectors=["worldbank"],
        keywords=["famine", "hunger", "poverty", "food crisis", "humanitarian",
                  "shortage"],
    ),
    "financial": Domain(
        "financial", "Economic Stress", ["H0"],
        collectors=["economic", "fred_news"],
        keywords=["inflation", "recession", "unemployment", "default", "debt",
                  "cbdc", "currency", "bank", "collapse"],
    ),
    "cosmic": Domain(
        "cosmic", "Cosmic & Space Weather", ["J6"],
        collectors=["spaceweather"],
        keywords=["solar", "geomagnetic", "flare", "storm", "aurora",
                  "radiation", "blackout"],
    ),
    "digital_control": Domain(
        "digital_control", "Commerce Control & Digital ID", ["B2"],
        collectors=["eff"],
        keywords=["biometric", "facial recognition", "digital id",
                  "surveillance", "cashless", "cbdc", "age verification"],
    ),
    "middle_east": Domain(
        "middle_east", "Middle East & Temple Mount", ["J3", "MS0"],
        collectors=["temple_mount"],
        keywords=["temple mount", "jerusalem", "israel", "third temple",
                  "sanctuary", "al-aqsa"],
    ),
    "antichrist": Domain(
        "antichrist", "Antichrist Patterns", ["MS0", "MS1", "AC0", "B1"],
        collectors=["antichrist_patterns"],
        keywords=["blasphemy", "man of sin", "lying wonders", "global ruler",
                  "image", "worship"],
    ),
    "persecution": Domain(
        "persecution", "Christian Persecution", ["J0"],
        collectors=["persecution"],
        keywords=["persecution", "church", "christian", "martyr", "blasphemy law"],
    ),
    "health": Domain(
        "health", "Pestilence & Health", ["J0"],
        collectors=["health"],
        keywords=["pandemic", "outbreak", "virus", "pestilence", "disease",
                  "epidemic"],
    ),
}


# Reverse index: collector name -> domain key.
COLLECTOR_TO_DOMAIN: Dict[str, str] = {
    collector: domain.key
    for domain in DOMAINS.values()
    for collector in domain.collectors
}


def domain_for_collector(collector: str) -> str:
    return COLLECTOR_TO_DOMAIN.get(collector, "war")


def node_label(node_id: str) -> str:
    node = NODES.get(node_id)
    return node.label if node else node_id


def node_scripture(node_id: str) -> str:
    node = NODES.get(node_id)
    return node.scripture if node else ""
