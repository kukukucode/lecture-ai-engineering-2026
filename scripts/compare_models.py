"""第1回発展課題：Geminiのモデル比較実験"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from time import perf_counter, sleep

from google import genai
from google.genai import errors

from app.config import get_api_key

MODELS = (
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
)

QUESTIONS = {
    "lora": "LoRAとは何ですか？",
    "levels": "AIE2026の講座の宿題にある「3レベル」とは何ですか？",
}

FIELDS = (
    "model", "question_id", "trial", "seconds",
    "input_tokens", "output_tokens",
    "thinking_tokens", "total_tokens", "answer"
)


def generate_with_retry(client, model, question):
    for attempt in range(1, 4):
        start = perf_counter()
        try:
            response = client.models.generate_content(
                model=model, contents=question
            )
            return response, perf_counter() - start
        except errors.APIError as e:
            if e.code != 503 or attempt == 3:
                raise
            wait = 20 * attempt
            print(f"503エラー。{wait}秒後に再試行します")
            sleep(wait)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--pause", type=float, default=15)
    parser.add_argument(
        "--output",
        default="results/lec01_experiment.csv"
    )
    args = parser.parse_args()

    if args.repeats < 1 or args.pause < 0:
        parser.error("repeatsは1以上、pauseは0以上にしてください")

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = set()
    durations = defaultdict(list)
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as old:
            for row in csv.DictReader(old):
                key = (row["model"], row["question_id"], int(row["trial"]))
                existing.add(key)
                durations[(row["model"], row["question_id"])].append(
                    float(row["seconds"])
                )
    client = genai.Client(api_key=get_api_key())
    completed = 0

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if path.stat().st_size == 0:
            writer.writeheader()

        for model in MODELS:
            for qid, question in QUESTIONS.items():
                for trial in range(1, args.repeats + 1):
                    if (model, qid, trial) in existing:
                        print(f"スキップ: {model} | {qid} | {trial}回目")
                        continue

                    if completed:
                        sleep(args.pause)

                    try:
                        response, elapsed = generate_with_retry(
                            client, model, question
                        )
                    except errors.APIError as e:
                        raise SystemExit(
                            f"APIエラー({e.code})で中断。結果は {path} に保存済み"
                        ) from e

                    usage = response.usage_metadata

                    row = {
                        "model": model,
                        "question_id": qid,
                        "trial": trial,
                        "seconds": round(elapsed, 3),
                        "input_tokens": getattr(
                            usage, "prompt_token_count", None
                        ),
                        "output_tokens": getattr(
                            usage, "candidates_token_count", None
                        ),
                        "thinking_tokens": getattr(
                            usage, "thoughts_token_count", None
                        ),
                        "total_tokens": getattr(
                            usage, "total_token_count", None
                        ),
                        "answer": response.text or "",
                    }

                    writer.writerow(row)
                    f.flush()

                    durations[(model, qid)].append(elapsed)
                    completed += 1

                    print(
                        f"{model} | {qid} | {trial}回目 | "
                        f"{elapsed:.3f}秒 | "
                        f"総{row['total_tokens']}tokens"
                    )

    print(f"\nCSV保存先: {path}")

    for (model, qid), values in durations.items():
        average = mean(values)
        spread = (
            f" / 標準偏差 {stdev(values):.3f}秒"
            if len(values) >= 2 else ""
        )
        print(
            f"{model} | {qid}: "
            f"平均 {average:.3f}秒{spread}"
        )


if __name__ == "__main__":
    main()
