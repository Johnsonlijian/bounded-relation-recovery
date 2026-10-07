"""Assemble the submission INFORMATICS_ARTEFACT bundle (no new computation)."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "submission" / "INFORMATICS_ARTEFACT"

CORE_FILES = [
    ("knowledge_graph.json", ROOT / "knowledge_graph.json"),
    ("outputs/knowledge_trace.csv", ROOT / "outputs" / "knowledge_trace.csv"),
    ("outputs/design_query_examples.csv", ROOT / "outputs" / "design_query_examples.csv"),
    ("outputs/channel_query_examples.csv", ROOT / "outputs" / "channel_query_examples.csv"),
    ("outputs/evidence_state.json", ROOT / "outputs" / "evidence_state.json"),
    ("outputs/result_summary.json", ROOT / "outputs" / "result_summary.json"),
    ("outputs/r02_protocol_validation_summary.json", ROOT / "outputs" / "r02_protocol_validation_summary.json"),
    ("outputs/r04_sr_baseline_summary.json", ROOT / "outputs" / "r04_sr_baseline_summary.json"),
    ("outputs/r04_dsm_demo_summary.json", ROOT / "outputs" / "r04_dsm_demo_summary.json"),
    ("outputs/r07_compression_index_contract.json", ROOT / "outputs" / "r07_compression_index_contract.json"),
    ("outputs/r07_compression_index_dataset.csv", ROOT / "outputs" / "r07_compression_index_dataset.csv"),
    ("outputs/r10_predicate_action_matrix.csv", ROOT / "outputs" / "r10_predicate_action_matrix.csv"),
    ("outputs/r10_global_scale_check.json", ROOT / "outputs" / "r10_global_scale_check.json"),
    ("outputs/r10_cross_table_modulus_transfer.csv", ROOT / "outputs" / "r10_cross_table_modulus_transfer.csv"),
    ("outputs/r10_theory_properties.json", ROOT / "outputs" / "r10_theory_properties.json"),
    ("data/source_table_transcription.csv", ROOT / "data" / "source_table_transcription.csv"),
    ("data/r07_compression_index_dataset.csv", ROOT / "data" / "r07_compression_index_dataset.csv"),
    ("src/brr/schema.py", ROOT / "src" / "brr" / "schema.py"),
    ("src/brr/actions.py", ROOT / "src" / "brr" / "actions.py"),
    ("src/brr/evaluate.py", ROOT / "src" / "brr" / "evaluate.py"),
    ("src/r07_compression_index_case.py", ROOT / "src" / "r07_compression_index_case.py"),
    ("src/r09_augment_geotechnical_graph.py", ROOT / "src" / "r09_augment_geotechnical_graph.py"),
    ("src/r10_super_uplift_evidence.py", ROOT / "src" / "r10_super_uplift_evidence.py"),
    ("figures/figure12_bounded_release_calculus.pdf", ROOT / "figures" / "figure12_bounded_release_calculus.pdf"),
    ("figures/figure12_bounded_release_calculus.svg", ROOT / "figures" / "figure12_bounded_release_calculus.svg"),
    ("figures/figure13_scale_nonidentification.pdf", ROOT / "figures" / "figure13_scale_nonidentification.pdf"),
    ("figures/figure13_scale_nonidentification.svg", ROOT / "figures" / "figure13_scale_nonidentification.svg"),
    ("paper_figures/figure_specs/r10_bounded_release_calculus.md", ROOT / "paper_figures" / "figure_specs" / "r10_bounded_release_calculus.md"),
    ("paper_figures/reviews/r10_figure_review.md", ROOT / "paper_figures" / "reviews" / "r10_figure_review.md"),
    ("paper_figures/reviews/r11_final_check_figure_review.md", ROOT / "paper_figures" / "reviews" / "r11_final_check_figure_review.md"),
]

DOC_FILES = [
    ("README.md", ROOT / "reproducibility" / "r10_informatics" / "README.md"),
    ("REPRODUCIBLE_RUNBOOK.md", ROOT / "reproducibility" / "r10_informatics" / "REPRODUCIBLE_RUNBOOK.md"),
    ("ACTION_TRACE_GUIDE.md", ROOT / "reproducibility" / "r10_informatics" / "ACTION_TRACE_GUIDE.md"),
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    if PKG.exists():
        shutil.rmtree(PKG)
    PKG.mkdir(parents=True, exist_ok=True)
    for rel, src in CORE_FILES:
        if not src.exists():
            print(f"missing {src}")
            continue
        dst = PKG / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"copied {rel}")
    for rel, src in DOC_FILES:
        if src.exists():
            dst = PKG / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
    manifest_files = []
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.name == "MANIFEST.json":
            continue
        manifest_files.append({
            "path": str(path.relative_to(PKG)).replace("\\", "/"),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        })
    manifest = {
        "package": "INFORMATICS_ARTEFACT",
        "purpose": "Submission-facing informatics deliverable for Advanced Engineering Informatics",
        "submission_state": "SUBMITTED (2026-10-07)",
        "ontology_version": json.loads((PKG / "knowledge_graph.json").read_text(encoding="utf-8")).get(
            "ontology_version", "unknown"
        ),
        "files": manifest_files,
    }
    (PKG / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {PKG / 'MANIFEST.json'} ({len(manifest_files)} files)")

if __name__ == "__main__":
    main()

