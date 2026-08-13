from pathlib import Path
import math
import re


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


def vectorize(tokens):
    vec = {}
    for token in tokens:
        vec[token] = vec.get(token, 0) + 1
    return vec


def cosine_similarity(a, b):
    if not a or not b:
        return 0.0

    vocab = set(a.keys()) | set(b.keys())

    dot = sum(a.get(k, 0) * b.get(k, 0) for k in vocab)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


def retrieve_wisdom(query, top_k=3):
    data_dir = Path("data")

    if not data_dir.exists():
        return "No emotional knowledge available."

    query_vec = vectorize(tokenize(query))
    results = []

    for file in data_dir.rglob("*.txt"):
        try:
            text = file.read_text(encoding="utf-8").strip()
            if not text:
                continue

            score = cosine_similarity(
                query_vec,
                vectorize(tokenize(text))
            )

            results.append((score, text))

        except Exception:
            continue

    if not results:
        return "No emotional knowledge available."

    results.sort(key=lambda x: x[0], reverse=True)

    top = [text for score, text in results[:top_k] if score > 0]

    if not top:
        top = [results[0][1]]

    return "\n\n".join(top)