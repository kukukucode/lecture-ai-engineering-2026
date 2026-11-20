"""Day 5 Advanced: Hybrid RAG retrieval tests without API calls."""

import json

import pytest

from app import hybrid


@pytest.fixture
def sample_data(monkeypatch, tmp_path):
    def page(page_id, title, section="Fine-Tuning", document="lec02-main"):
        return {
            "page_id": page_id,
            "document_id": document,
            "lecture": 2,
            "section": section,
            "title": title,
            "content": title,
        }

    pages = [
        page("lec02-main-p046", "小規模なFTとRAGの使い分け"),
        page("lec02-main-p052", "LoRA QLoRAの仕組み"),
        page("lec02-main-p051", "PEFTとLoRA QLoRA"),
        page("lec02-main-p055", "FTの落とし穴"),
        page("lec02-main-p060", "注意点", section="演習"),
        page("lec03-main-p001", "注意点", document="lec03-main"),
    ]

    seeds = [
        {**pages[0], "distance": 0.1},
        {**pages[1], "distance": 0.2},
    ]

    graph = {
        "edges": [
            {
                "source": "lec02-main-p052",
                "target": "lec02-main-p051",
                "relation": "next_page",
            },
            {
                "source": "lec02-main-p046",
                "target": "term:fine-tuning",
                "relation": "mentions",
            },
            {
                "source": "lec02-main-p055",
                "target": "term:fine-tuning",
                "relation": "mentions",
            },
            {
                "source": "lec02-main-p052",
                "target": "lec02-main-p060",
                "relation": "next_page",
            },
            {
                "source": "lec02-main-p052",
                "target": "lec03-main-p001",
                "relation": "next_page",
            },
        ]
    }

    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")

    monkeypatch.setattr(hybrid, "RAG_GRAPH", graph_path)
    monkeypatch.setattr(hybrid, "load_pages", lambda: pages)
    monkeypatch.setattr(hybrid, "vector_search", lambda query: seeds)

    return seeds


def test_composite_query_adds_missing_evidence(sample_data):
    result = hybrid.hybrid_search("LoRA QLoRA 仕組み 注意点")

    added = {p["page_id"] for p in result["added"]}
    assert added == {"lec02-main-p051", "lec02-main-p055"}

    ids = [p["page_id"] for p in result["results"]]
    assert len(ids) == len(set(ids))


def test_simple_query_does_not_expand(sample_data):
    result = hybrid.hybrid_search("LoRA QLoRA 違い")

    assert result["added"] == []
    assert result["results"] == sample_data


def test_expansion_is_bounded_and_preserves_baseline(sample_data):
    result = hybrid.hybrid_search(
        "LoRA QLoRA 仕組み 注意点",
        max_added=1,
    )

    assert len(result["added"]) == 1
    assert result["results"][:2] == sample_data
    assert len(result["results"]) == 3

    added_id = result["added"][0]["page_id"]
    assert added_id in {
        "lec02-main-p051",
        "lec02-main-p055",
    }
