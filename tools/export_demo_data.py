"""Export only the five selected showcase cases from a local research corpus.

The source corpus is intentionally not part of this repository.  Run this
script only when rebuilding the local showcase dataset from the original files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def compact_case(row: dict) -> dict:
    charge = row.get("JCHARGE", "未標示")
    return {
        "id": str(row.get("ID", "")).replace("_", " "),
        "graph_id": row.get("graph_id", ""),
        "charge": charge,
        "article": row.get("JARTICLE", "未標示"),
        "title": row.get("JTITLE", ""),
        # The original judgment-summary field may expose a party's name.
        # A portfolio demo instead uses a neutral, non-identifying summary.
        "main": f"此展示案例涉及{charge}；請參閱下方去識別化事實與事件圖，了解案件脈絡與相近案例比較。",
        "fact": row.get("JFACT", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Folder containing the original JSON/JSONL files")
    parser.add_argument("output", type=Path, help="Output JSON path")
    args = parser.parse_args()
    source = args.source

    manifest = json.loads(
        (Path(__file__).resolve().parents[1] / "assets" / "drawio" / "showcase_manifest.json").read_text(encoding="utf-8")
    )
    selected_ids = {item["query_graph_id"] for item in manifest}
    retrievals = [
        row for row in json.loads((source / "標記相似案例資料庫.json").read_text(encoding="utf-8"))
        if row["query_graph_id"] in selected_ids
    ]
    history_ids = {
        item["similar_graph_id"]
        for row in retrievals
        for item in row.get("top_5_retrieved", [])
    }

    queries = {
        row["graph_id"]: compact_case(row)
        for row in read_jsonl(source / "test_with_graph_pdf.jsonl")
        if row.get("graph_id") in selected_ids
    }
    histories = {}
    for row in read_jsonl(source / "train_with_graph_pdf.jsonl"):
        if row.get("graph_id") in history_ids:
            histories[row["graph_id"]] = compact_case(row)

    needed_graphs = selected_ids | history_ids
    graphs = {}
    for row in read_jsonl(source / "all_crimes_feg.jsonl"):
        if row.get("graph_id") in needed_graphs:
            graphs[row["graph_id"]] = {"nodes": row.get("nodes", []), "edges": row.get("edges", [])}

    llm = {}
    for row in read_jsonl(source / "LLM推理.jsonl"):
        if row.get("query_graph_id") in selected_ids:
            llm[row["query_graph_id"]] = {
                "prediction": row.get("llm_prediction", {}),
                "ground_truth": row.get("ground_truth", {}),
                "is_correct": row.get("is_correct"),
                "reasoning": row.get("full_reasoning_report", ""),
            }

    output = {
        "queries": queries,
        "histories": histories,
        "graphs": graphs,
        "retrievals": {row["query_graph_id"]: row for row in retrievals},
        "llm": llm,
        "showcase": {item["query_graph_id"]: item for item in manifest},
        "query_list": [
            {"graph_id": item["query_graph_id"], "id": queries[item["query_graph_id"]]["id"], "charge": queries[item["query_graph_id"]]["charge"]}
            for item in manifest
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(queries)} queries and {len(histories)} reference cases to {args.output}")


if __name__ == "__main__":
    main()
