import json
from pathlib import Path
from collections import Counter

MEMORY_FILE = Path("memory/memories.json")
PROFILE_FILE = Path("memory/profile.json")
JOURNAL_FILE = Path("memory/journal.json")
SUMMARY_FILE = Path("memory/session_summary.json")


# -----------------------------
# Conversation Memory
# -----------------------------
def load_memories():
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_memories(memories):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(
        json.dumps(memories, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def remember(text):
    memories = load_memories()

    if text not in memories:
        memories.append(text)

    memories = memories[-50:]
    save_memories(memories)


def memory_context():
    memories = load_memories()

    if not memories:
        return "No important memories yet."

    return "\n".join(f"- {m}" for m in memories[-10:])


# -----------------------------
# Emotional Profile
# -----------------------------
def load_profile():
    if PROFILE_FILE.exists():
        try:
            profile = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            profile = {}
    else:
        profile = {}

    profile.setdefault("patterns", {})
    profile.setdefault("recent_emotions", [])
    profile.setdefault("important_beliefs", [])
    profile.setdefault("conversation_count", 0)

    return profile


def save_profile(profile):
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def update_profile(user_input, emotion):
    profile = load_profile()

    profile["conversation_count"] += 1

    profile["recent_emotions"].append(emotion)
    profile["recent_emotions"] = profile["recent_emotions"][-30:]

    text = user_input.lower()

    def add(name):
        profile["patterns"][name] = profile["patterns"].get(name, 0) + 1

    if any(w in text for w in [
        "tired", "exhausted", "drained", "burnt out",
        "burned out", "no energy"
    ]):
        add("burnout")

    if any(w in text for w in [
        "compare", "behind", "everyone else",
        "others are", "falling behind"
    ]):
        add("comparison")

    if any(w in text for w in [
        "guilty", "my fault", "i ruined", "i messed up",
        "sorry"
    ]):
        add("self_blame")

    if any(w in text for w in [
        "lonely", "alone", "no one", "isolated"
    ]):
        add("loneliness")

    if any(w in text for w in [
        "worthless", "failure", "useless", "not enough",
        "i'm the problem"
    ]):
        add("low_self_worth")

    if any(w in text for w in [
        "parents", "family", "mother", "father",
        "expectations"
    ]):
        add("family_pressure")

    if any(w in text for w in [
        "perfect", "perfection", "need to do better",
        "not good enough"
    ]):
        add("perfectionism")

    save_profile(profile)


def profile_context():
    profile = load_profile()

    patterns = profile.get("patterns", {})
    emotions = profile.get("recent_emotions", [])

    lines = []

    if patterns:
        for name, count in sorted(
            patterns.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if count >= 2:
                lines.append(f"- {name} has appeared {count} times")

    if emotions:
        common = Counter(emotions).most_common(3)
        lines.append("Recent emotional trend:")
        for emotion, count in common:
            lines.append(f"- {emotion}: {count}")

    if not lines:
        return "No strong emotional patterns yet."

    return "\n".join(lines)


# -----------------------------
# Session Summary
# -----------------------------
def load_session_summary():
    if SUMMARY_FILE.exists():
        try:
            return json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_session_summary(summary):
    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def update_session_summary():
    profile = load_profile()

    patterns = profile.get("patterns", {})
    emotions = profile.get("recent_emotions", [])

    dominant_emotion = None
    if emotions:
        dominant_emotion = Counter(emotions).most_common(1)[0][0]

    top_patterns = sorted(
        patterns.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    summary = {
        "primary_emotion": dominant_emotion,
        "top_patterns": [p for p, _ in top_patterns],
        "conversation_count": profile.get("conversation_count", 0)
    }

    save_session_summary(summary)


def session_summary_context():
    summary = load_session_summary()

    if not summary:
        return "No session summary available."

    lines = []

    if summary.get("primary_emotion"):
        lines.append(f"Primary emotion: {summary['primary_emotion']}")

    if summary.get("top_patterns"):
        lines.append(
            "Recurring themes: " +
            ", ".join(summary["top_patterns"])
        )

    return "\n".join(lines)


# -----------------------------
# Vexa Private Journal
# -----------------------------
def load_journal():
    if JOURNAL_FILE.exists():
        try:
            return json.loads(JOURNAL_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_journal(entries):
    JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL_FILE.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def add_journal_entry(entry):
    journal = load_journal()

    journal.append(entry)
    journal = journal[-40:]

    save_journal(journal)


def journal_context():
    journal = load_journal()

    if not journal:
        return "No journal reflections yet."

    return "\n".join(f"- {e}" for e in journal[-5:])


# -----------------------------
# Memory Extraction
# -----------------------------
def extract_memory(user_input, emotion):
    text = user_input.lower()
    memories = []

    if any(w in text for w in [
        "parents", "family", "mother", "father"
    ]):
        memories.append("User often feels pressure from family expectations.")

    if any(w in text for w in [
        "compare", "behind", "everyone else"
    ]):
        memories.append("User often compares themselves to others.")

    if any(w in text for w in [
        "tired", "exhausted", "drained", "burnt out"
    ]):
        memories.append("User has been feeling deeply exhausted lately.")

    if any(w in text for w in [
        "guilty", "my fault", "sorry"
    ]):
        memories.append("User tends to blame themselves when things go wrong.")

    if any(w in text for w in [
        "lonely", "alone", "no one"
    ]):
        memories.append("User has been feeling lonely recently.")

    if any(w in text for w in [
        "worthless", "failure", "useless", "not enough"
    ]):
        memories.append("User struggles with their sense of self-worth.")

    if any(w in text for w in [
        "perfect", "perfection", "need to do better"
    ]):
        memories.append("User puts a lot of pressure on themselves to be perfect.")

    return memories