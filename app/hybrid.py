"""Day 5 Advanced: bounded Tree/Graph expansion of vector-RAG evidence."""

import argparse
import json
import re
from collections import defaultdict, deque
from time import perf_counter

from app.config import RAG_GRAPH
from app.retrieval import load_pages, search as vector_search


def hybrid_search(query: str, max_added: int = 2) -> dict:
    """Keep vector results; add a few evidence pages connected in the same chapter."""
    seeds = vector_search(query)
    pages = {p["page_id"]: p for p in load_pages()}
    selected = {p["page_id"] for p in seeds}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    links = defaultdict(set)

    for edge in graph["edges"]:
        if edge["relation"] in ("mentions", "next_page"):
            a, b = edge["source"], edge["target"]
            links[a].add(b)
            links[b].add(a)

    candidates = {}
    for seed in seeds:
        root = seed["page_id"]
        queue = deque([(root, 0)])
        visited = {root}

        while queue:
            current, hops = queue.popleft()
            if hops == 2:
                continue

            for neighbor in sorted(links[current]):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append((neighbor, hops + 1))

                if neighbor not in pages or neighbor in selected:
                    continue

                page = pages[neighbor]
                if (page["document_id"], page["section"]) != (
                    seed["document_id"], seed["section"]
                ):
                    continue

                candidates[neighbor] = min(
                    candidates.get(neighbor, 3), hops + 1
                )

    risk = any(
        word in query
        for word in ("注意", "リスク", "落とし穴", "失敗", "懸念")
    )
    mechanism = "仕組み" in query and bool(
        re.search(r"(?:LoRA|QLoRA|PEFT)", query, re.I)
    )

    risk_words = ("落とし穴", "注意", "リスク", "失敗", "副作用")
    risk_uncovered = risk and not any(
        any(word in seed["title"] for word in risk_words)
        for seed in seeds
    )
    mech_uncovered = mechanism and not any(
        "PEFT" in seed["title"] for seed in seeds
    )

    tokens = set(re.findall(r"[a-z][a-z0-9-]*", query.casefold()))

    def score(page_id: str):
        page = pages[page_id]
        title = page["title"].casefold()
        body = page["content"].casefold()

        lexical = sum(
            3 if token in title else 1 if token in body else 0
            for token in tokens
        )

        risk_bonus = (
            12 if risk_uncovered
            and any(word in page["title"] for word in risk_words)
            else 0
        )
        mechanism_bonus = (
            9 if mech_uncovered and "peft" in title else 0
        )

        return (
            risk_bonus
            + mechanism_bonus
            + lexical
            - 0.3 * candidates[page_id],
            risk_bonus + mechanism_bonus,
        )

    ranked = sorted(
        candidates,
        key=lambda page_id: (-score(page_id)[0], page_id),
    )

    added = []
    for page_id in ranked:
        value, bonus = score(page_id)

        if bonus == 0 or value < 1:
            continue

        added.append({
            **pages[page_id],
            "source": "tree_graph_expansion",
            "hops": candidates[page_id],
        })

        if len(added) >= max_added:
            break

    return {"results": seeds + added, "added": added}


def search_materials(query: str) -> str:
    """Search lecture materials and selectively expand missing evidence via Tree/Graph."""
    return json.dumps(
        {"results": hybrid_search(query)["results"]},
        ensure_ascii=False,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()

    if args.inspect:
        hits = hybrid_search(args.question)

        for item in hits["results"]:
            label = "ADDED" if item in hits["added"] else "BASE"
            print(f"{label:5} {item['page_id']} | {item['title']}")
        return

    from app.agent import agent, build_model, print_trace

    started = perf_counter()

    with agent.override(tools=[search_materials]):
        result = agent.run_sync(
            args.question,
            model=build_model(),
        )

    print(result.output)
    print_trace(result, perf_counter() - started)


if __name__ == "__main__":
    main()
