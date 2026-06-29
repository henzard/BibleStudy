#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evidence graph + clustering.

Rather than reasoning over isolated headlines, we link events that share
entities or keywords within a research domain, then take connected components
as :class:`EvidenceCluster` objects. Each cluster is a small "situation" that
multiple events — ideally from multiple sources — speak to.

The number of *distinct sources* in a cluster is the cross-validation signal
used later for confidence (one source = weak, three+ = strong).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List

from .models import NormalizedEvent, EvidenceCluster
from .taxonomy import DOMAINS


class _UnionFind:
    def __init__(self, items: List[str]):
        self.parent = {item: item for item in items}

    def find(self, x: str) -> str:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def _link_features(event: NormalizedEvent) -> List[str]:
    """Features that, when shared, indicate two events are about the same
    underlying situation.

    We link on **entities** (locations / proper nouns) only. Domain keywords
    such as "earthquake" or "magnitude" are deliberately excluded: they merely
    restate the domain (which we already group by) and would over-merge every
    event into a single blob.
    """
    return [f"ent:{e.lower()}" for e in event.entities]


def build_clusters(events: List[NormalizedEvent]) -> List[EvidenceCluster]:
    """Group events into evidence clusters per domain via connected
    components over shared features."""
    by_domain: Dict[str, List[NormalizedEvent]] = defaultdict(list)
    for ev in events:
        by_domain[ev.domain].append(ev)

    clusters: List[EvidenceCluster] = []
    for domain_key, domain_events in by_domain.items():
        if not domain_events:
            continue

        uf = _UnionFind([ev.event_id for ev in domain_events])
        feature_index: Dict[str, str] = {}  # feature -> first event id seen
        for ev in domain_events:
            for feat in _link_features(ev):
                if feat in feature_index:
                    uf.union(ev.event_id, feature_index[feat])
                else:
                    feature_index[feat] = ev.event_id

        groups: Dict[str, List[NormalizedEvent]] = defaultdict(list)
        for ev in domain_events:
            groups[uf.find(ev.event_id)].append(ev)

        domain_title = DOMAINS[domain_key].title if domain_key in DOMAINS else domain_key
        for idx, members in enumerate(sorted(
                groups.values(), key=lambda g: -len(g))):
            entity_counts = Counter(
                e for ev in members for e in ev.entities
            )
            top_entities = [e for e, _ in entity_counts.most_common(4)]
            label = top_entities[0] if top_entities else domain_title
            node_ids = sorted({ev.node_id for ev in members if ev.node_id})
            clusters.append(
                EvidenceCluster(
                    cluster_id=f"{domain_key}-{idx}",
                    domain=domain_key,
                    label=label,
                    node_ids=node_ids or DOMAINS.get(
                        domain_key, DOMAINS["war"]).node_ids,
                    events=sorted(
                        members,
                        key=lambda e: (e.occurred_at or "", e.magnitude or 0),
                        reverse=True,
                    ),
                    entities=top_entities,
                )
            )

    # Strongest situations first: more sources, then more events.
    clusters.sort(key=lambda c: (c.source_count, c.size), reverse=True)
    return clusters
