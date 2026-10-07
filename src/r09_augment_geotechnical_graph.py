from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "outputs" / "r07_compression_index_contract.json"
GRAPH = ROOT / "knowledge_graph.json"
TRACE = ROOT / "outputs" / "knowledge_trace.csv"
EVIDENCE = ROOT / "outputs" / "evidence_state.json"

def augment_graph() -> None:
    geo = json.loads(CONTRACT.read_text(encoding="utf-8"))
    kg = json.loads(GRAPH.read_text(encoding="utf-8"))
    kg["ontology_version"] = "1.4"
    kg["scope"] = (
        "knowledge-constrained recovery protocol demonstrated on cold-formed steel "
        "and geotechnical relations"
    )
    prov = kg.setdefault("provenance", {})
    prov["independent_geotechnical_case"] = {
        "source": geo["source"],
        "contract": geo["contract"],
        "action_summary": geo.get("action_summary", {}),
        "scope": "cross-domain direct-response correlation screen; no solver selector required",
    }
    ev = kg.setdefault("evidence_classes", {})
    ev["cross_domain_case_evidence"] = (
        "Uzer 2024 independent oedometer table; nine published e0-only correlations; "
        "two positivity rejects and seven bounded retains through the shared reducer"
    )
    node_ids = {n["id"] for n in kg.get("nodes", [])}
    nodes = [
        {"id": "GeotechnicalSoil", "kind": "engineering_object",
         "attributes": ["normally consolidated fine-grained soil"]},
        {"id": "VoidRatio", "kind": "dimensionless_state", "definition": "e0",
         "domain": geo["contract"]["declared_domain"]},
        {"id": "CompressionIndex", "kind": "response", "definition": "Cc", "unit": "-"},
        {"id": "PublishedCcCorrelation", "kind": "candidate_relation",
         "definition": "nine attributed e0-only correlations"},
        {"id": "OedometerCell", "kind": "experimental_evidence",
         "definition": "independent printed Table A2 cell +/- 0.0005"},
    ]
    for node in nodes:
        if node["id"] not in node_ids:
            kg.setdefault("nodes", []).append(node)
    existing_relations = {tuple(r) for r in kg.get("relations", [])}
    for rel in [
        ["GeotechnicalSoil", "defines", "VoidRatio"],
        ["VoidRatio", "enters", "PublishedCcCorrelation"],
        ["PublishedCcCorrelation", "predicts", "CompressionIndex"],
        ["OedometerCell", "tests", "PublishedCcCorrelation"],
        ["CompressionIndex", "supports", "DesignAction"],
    ]:
        if tuple(rel) not in existing_relations:
            kg.setdefault("relations", []).append(rel)
    rule_ids = {r.get("id") for r in kg.get("rules", [])}
    for rule in [
        {"id": "R11", "if": "a published response is non-positive on its declared observed domain",
         "then": "reject_nonexecutable"},
        {"id": "R12", "if": "a direct-response correlation misses the displayed interval while mechanics pass",
         "then": "retain_bounded_claim"},
        {"id": "R13", "if": "no numerical solver selector is required by the direct-response source",
         "then": "record selector as not applicable; do not invent one"},
    ]:
        if rule["id"] not in rule_ids:
            kg.setdefault("rules", []).append(rule)
    run_ids = {r.get("run_id") for r in kg.get("runs", [])}
    if "geotechnical_compression_index" not in run_ids:
        kg.setdefault("runs", []).append({
            "run_id": "geotechnical_compression_index",
            "object": "GeotechnicalSoil",
            "state": "VoidRatio",
            "response": "CompressionIndex",
            "relation": {
                "id": "PublishedCcCorrelation",
                "candidate_class": "nine published e0-only correlations",
                "domain": geo["contract"]["declared_domain"],
            },
            "predicates": {
                "mechanics.positivity": "relation-specific",
                "mechanics.monotonicity": "relation-specific",
                "mechanics.finiteness": True,
                "evidence.interval_feasibility": False,
                "provenance.selector_verified": "not applicable",
            },
            "evidence": {
                "cells": geo["contract"]["cells_parsed"],
                "displayed_half_unit": geo["contract"]["displayed_half_unit"],
                "action_summary": geo.get("action_summary", {}),
            },
            "action": "heterogeneous; see outputs/r07_compression_index_contract.json",
            "scope": "observed Table A2 domain only; transcribed cells and direct-response interval predicate",
        })
    GRAPH.write_text(json.dumps(kg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def augment_trace() -> None:
    row = (
        "a second domain runs through the shared action reducer,R11+R12+R13,"
        "Uzer 2024 Table A2; 445 cells; nine competing e0-only correlations,"
        "cross_domain_action_reducer_pass"
    )
    text = TRACE.read_text(encoding="utf-8").rstrip("\n")
    if "a second domain runs through the shared action reducer" not in text:
        text += "\n" + row
    TRACE.write_text(text + "\n", encoding="utf-8")

def augment_evidence() -> None:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    data["revision_date"] = "2026-10-07"
    data["cross_domain_case_evidence"] = (
        "available; Uzer 2024 Table A2; 445 cells; nine competing correlations; shared reducer"
    )
    data["geotechnical_case_action_summary"] = json.loads(
        CONTRACT.read_text(encoding="utf-8")
    ).get("action_summary", {})
    data["geotechnical_case_boundary"] = json.loads(
        CONTRACT.read_text(encoding="utf-8")
    ).get("boundary", "")
    EVIDENCE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

if __name__ == "__main__":
    augment_graph()
    augment_trace()
    augment_evidence()
    print("augmented graph, trace and evidence state with geotechnical case")

