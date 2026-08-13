import os
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from memory.memory_manager import (
    remember,
    memory_context,
    update_profile,
    profile_context,
    add_journal_entry,
    journal_context,
    extract_memory,
)
from rag.retrieve import retrieve_wisdom

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

with open("personality/vexa_constitution.txt", "r", encoding="utf-8") as f:
    VEXA_CONSTITUTION = f.read()


# -----------------------------
# Helpers
# -----------------------------
def avoid_repetition(reply):
    previous = [
        msg for role, msg in st.session_state.get("messages", [])
        if role == "assistant"
    ]

    if not previous:
        return reply

    last = previous[-1].lower()
    current = reply.lower()

    repeated_phrases = [
        "that sounds",
        "i'm here",
        "you don't have to",
        "it's okay",
        "i don't think"
    ]

    for phrase in repeated_phrases:
        if phrase in last and phrase in current:
            current = current.replace(phrase, "").strip()

    return current.capitalize() if current else reply


def clean_reply(reply):
    # Remove leaked moderation/debug text
    reply = re.sub(r"User safety:\s*(safe|unsafe)", "", reply, flags=re.IGNORECASE)
    reply = re.sub(r"Safety:\s*(safe|unsafe)", "", reply, flags=re.IGNORECASE)
    reply = re.sub(r"Moderation:\s*.*", "", reply, flags=re.IGNORECASE)

    # Remove extra blank lines
    reply = re.sub(r"\n{2,}", "\n\n", reply)

    return reply.strip()


def detect_emotion(text):
    text = text.lower()

    emotions = {
        "sadness": [
            "sad", "cry", "lonely", "empty", "hurt",
            "depressed", "worthless", "hopeless", "down"
        ],
        "fear": [
            "anxious", "worried", "panic", "fear", "scared", "nervous"
        ],
        "anger": [
            "angry", "mad", "furious", "hate", "annoyed", "frustrated"
        ],
        "guilt": [
            "guilty", "sorry", "regret", "ashamed", "my fault"
        ],
        "joy": [
            "happy", "excited", "grateful", "love", "peaceful", "hopeful"
        ]
    }

    scores = {k: 0 for k in emotions}

    for emotion, words in emotions.items():
        for word in words:
            if word in text:
                scores[emotion] += 1

    detected = max(scores, key=scores.get)

    if scores[detected] == 0:
        return "neutral"

    return detected


# -----------------------------
# Main Vexa function
# -----------------------------
def vexa_reply(user_input):
    emotion = detect_emotion(user_input)
    update_profile(user_input, emotion)

    memories = memory_context()
    profile = profile_context()
    wisdom = retrieve_wisdom(user_input)
    journal = journal_context()

    history = st.session_state.get("messages", [])[-8:]

    messages = [
        {"role": "system", "content": VEXA_CONSTITUTION},
        {
            "role": "system",
            "content": f"""
User profile:
{profile}

Relevant memories:
{memories}

Recent journal:
{journal}

Relevant wisdom:
{wisdom}

Current emotion:
{emotion}

Think privately before replying.

- What emotion is underneath the user's words?
- Do they need comfort, clarity, advice, or simply presence?
- Are they criticizing themselves?
- Have they shown this pattern before?

Never reveal this reasoning.

Reply naturally.
Keep replies between 8 and 30 words unless the user asks for more.
Sound like a thoughtful therapist who speaks like a normal human.
Avoid therapy clichés.
Avoid motivational speeches.
Ask at most one meaningful question.
"""
        }
    ]

    for role, msg in history:
        messages.append({
            "role": "assistant" if role == "assistant" else "user",
            "content": msg
        })

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=messages,
    )

    reply = response.choices[0].message.content.strip()

    # Remove leaked moderation text
    reply = clean_reply(reply)

    # Reduce repetition
    reply = avoid_repetition(reply)

    # Keep responses short
    if len(reply.split()) > 32:
        reply = " ".join(reply.split()[:32])

    # Store meaningful memories
    for memory in extract_memory(user_input, emotion):
        remember(memory)

    # Private journal entry
    journal_prompt = f"""
Write one short observation (max 15 words) about the user.

User: {user_input}
Emotion: {emotion}

Only write the observation.
"""

    try:
        journal_response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "system",
                    "content": "Write concise emotional observations."
                },
                {"role": "user", "content": journal_prompt},
            ],
        )

        journal_entry = clean_reply(
            journal_response.choices[0].message.content.strip()
        )

        if journal_entry:
            add_journal_entry(journal_entry)

    except Exception:
        pass

    return reply


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Vexa", page_icon="🖤")

st.title("🖤 Vexa")
st.caption("An emotionally adaptive AI companion that remembers, reflects, and responds with quiet wisdom.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(msg)

user_input = st.chat_input("Talk to Vexa...")

if user_input:
    st.session_state.messages.append(("user", user_input))

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Vexa is thinking..."):
            reply = vexa_reply(user_input)
            st.markdown(reply)

    st.session_state.messages.append(("assistant", reply))