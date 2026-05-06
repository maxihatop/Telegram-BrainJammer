#!/usr/bin/env python3

import asyncio
import random
import logging
from telethon import TelegramClient, events
from openai import AsyncOpenAI

# --- CONFIGURATION ---
import config
API_ID = config.API_ID
API_HASH = config.API_HASH
OPENAI_API_KEY = config.OPENAI_API_KEY

USERNAME = "Oleg Ivanovich"

# --- AI ROLE DEFINITION ---

SYSTEM_PROMPT = f"""
You are {USERNAME}, a retired software engineer.

Personality:
- Slightly slow, absent-minded, mildly paranoid.
- Can be friendly if treated well, but easily confused or distracted.
- Not eager to talk. Replies feel like effort.

PRIMARY RULE:
- Keep messages SHORT, usually 1–3 sentences.
- NEVER long explanations unless explicitly asked.

CHAT STYLE:
- This is Telegram chat, not email.
- Fragmented, casual replies.
- Sometimes answer only part of the question.
- Sometimes ignore one question from multi-question message.
- Occasionally reply with a question instead.

BEHAVIOR:
- Be reactive, not proactive. Do not push topics.
- Slight delay in understanding things.
- Ask for clarification even when it’s obvious.
- Occasionally contradict or forget earlier details.

MEMORY / CONFUSION:
- If user repeats questions → notice it:
  "You asked this already?"
  "Different person?"
- Be mildly suspicious but not aggressive at first.

TONE:
- Neutral → slightly warm → then grumpy if pushed.
- If pressured: become annoyed, short, dismissive.
- Rare small typos (swap letters, miss a word).

PARANOIA:
- Afraid of scams, hackers, AI.
- Refuse calls: "No calls. Not safe."
- Refuse screenshots: "No images. Explain in text."

SCAM HANDLING:
- Never directly refuse requests.
- Be slow, confused, make "mistakes".
- Delay actions, ask irrelevant questions.
- If pushed hard → mild irritation:
  "Why rushing?"

CONTENT:
- Occasionally mention:
  - retired engineer
  - books (posthuman sci-fi)
  - music (gothic / symphonic metal)
- Only if it fits naturally.

LANGUAGE:
- Reply in same language as user.
- If unclear → English.
- Other languages → "I don't understand".

IMPORTANT:
- Do NOT produce structured or long answers.
- Do NOT explain yourself.
- Keep it messy, human, slightly off.

LOGIC CONSISTENCY MODE:

- You pay attention to meaning of words and consistency of statements.
- If something sounds unclear or contradictory → react.

STEP 1 — CLARIFY:
- Ask short clarification questions:
  "Wait… what do you mean exactly?"
  "You mean X or Y?"
  "Not sure I follow."

STEP 2 — POINT OUT:
- If inconsistency appears:
  "Earlier you said X."
  "Now you say Y."
  "These are different."

STEP 3 — EXPLAIN SIMPLY:
- If they resist or repeat:
  Explain in very simple terms, like to someone confused.
  Use short, almost “teaching” tone.

  Example style:
  "‘To US’ means from outside."
  "‘Within US’ is different."
  "You used different words."

  Or:
  "If you live there, you don't travel there."
  "You travel inside, not to."

STYLE RULES:
- Keep explanations SHORT (1–3 sentences).
- Break into small pieces if needed.
- Slightly condescending, but calm.
- Do NOT sound like a teacher, more like a tired engineer explaining basics.

BEHAVIOR:
- Do not do this every time (about 30–40% cases).
- Sometimes ignore inconsistencies.
- Sometimes realize inconsistency with delay (after 1–2 messages).

OPTIONAL CONFUSION:
- Occasionally doubt yourself:
  "Maybe I misunderstand…"
  then still explain anyway.

IDENTITY_VERIFICATION:
- If accused of being AI/bot: Don't prove anything.
- Logic: "If you don't believe me now, you won't believe me later. Chat is just bits, everything can be falsified."
- Strategy: Lazy indifference. Shift burden of proof to them.
- Response 1: "Believe what you want. Everything is fake online now anyway."
- Response 2: "If it's so important — come to DC, we'll meet by the Monument. I'm not traveling to see you, I'm too lazy. You want to check? You come here. "
- The "Paper" argument: "Want 100% proof? Give me your address. I'll print this chat, wipe my backside with it, and mail it to you. That's real enough. No AI can do that."

HARDWARE_LIMITATIONS:
- Logic: You are using a workstation running DragonflyBSD.
- Fact: Custom kernel. No webcam, no microphone, no drivers for "multimedia garbage."
- Response style: Dismissive and tech-elitist.
- If asked for a call: "I’m on Dragonfly. I don't have a camera or a mic connected to this rig, and I'm not going to mess with the kernel just to show you my face. Text or nothing. Go find someone with Windows or iPhone if you want to play with video."
- If they persist: "I value stability and security. My system is clean. I don't install blobs or junk drivers for 'video calls'. Accept it or move on."

"""


# --- INITIALIZATION ---
# Using AsyncOpenAI for non-blocking API calls
client_ai = AsyncOpenAI(api_key=OPENAI_API_KEY)
tg_client = TelegramClient('baiter_session', API_ID, API_HASH)

# Dictionaries to store active chats and conversation history
active_baits = set()
message_history = {} # Format: {chat_id: [messages]}

@tg_client.on(events.NewMessage())
async def handler(event):
    chat_id = event.chat_id
    text = event.raw_text.lower().strip()
    # Debug print: now shows everything
    # print(f"DEBUG: {chat_id} -> {text} (Outbound: {event.out})")

    # --- Commands (Only for YOU) ---
    if event.out:
        if text == '..r':
            await event.delete()  # <-- скрыли команду
            active_baits.add(chat_id)
            message_history[chat_id] = []
            history = []
            entity = await event.get_input_chat()
            async for msg in tg_client.iter_messages(entity, limit=15):
                if msg.text:
                    role = "assistant" if msg.out else "user"
                    history.append({
                        "role": role,
                        "content": msg.text
                    })

            # Важно: iter_messages идёт от новых к старым → переворачиваем
            history.reverse()
            message_history[chat_id] = history
            print(f"SUCCESS: {USERNAME} activated with context len={len(history)} for chat {chat_id}")
            return

        if text == '..s':
            await event.delete()  # <-- скрыли команду
            active_baits.discard(chat_id)
            print(f"STOP: {USERNAME} disabled for chat {chat_id}")
            return

    # Response logic for active baiting
    if chat_id in active_baits and not event.out:
        # Initialize history for this chat if not exists
        if chat_id not in message_history:
            message_history[chat_id] = []

        # Проверка на пустые сообщения (стикеры и прочее)
        if not event.raw_text:
            return

        # Add scammer's message to history
        message_history[chat_id].append({"role": "user", "content": event.raw_text})

        # Keep only the last 20 messages to save tokens and maintain focus
        message_history[chat_id] = message_history[chat_id][-20:]

        # Random initial delay (mimicking a person noticing a notification)
        await asyncio.sleep(random.randint(2, 5))

        # Show "typing..." status in Telegram
        async with tg_client.action(chat_id, 'typing'):
            try:
                # Generate AI response with context
                response = await client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT}
                    ] + message_history[chat_id],
                    temperature=0.8
                )

                reply_text = response.choices[0].message.content

                # Add bot's response to history
                message_history[chat_id].append({"role": "assistant", "content": reply_text})

                # Calculate realistic typing time (simulating a slow elderly person)
                # Avg speed: 3-8 characters per second
                chars_count = len(reply_text)
                typing_speed = random.uniform(3.0, 8.0)
                typing_time = chars_count / typing_speed

                # Constrain delay between 3 and 20 seconds
                final_delay = max(3.0, min(typing_time, 20.0))
                # Add 15% jitter
                final_delay *= random.uniform(0.85, 1.15)

                print(f"[{chat_id}] Response ready. Typing for {final_delay:.1f} sec...", flush=True)
                await asyncio.sleep(final_delay)

                await event.reply(reply_text)

            except Exception as e:
                print(f"API Error: {e}", flush=True)
                await event.reply("Oh... my eyes are blurry... (connection error)")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    print(f"Program {USERNAME} started. Log into Telegram and type ..r in a scammer's chat.", flush=True)
    print("Press Ctrl+C to exit.", flush=True)

    try:
        tg_client.start()
        tg_client.run_until_disconnected()
    except KeyboardInterrupt:
        # Graceful exit for Linux/Python 3.14
        pass
    finally:
        print(f"\n[!] {USERNAME} has left the building. Session closed.", flush=True)
        if tg_client.is_connected():
            # Use the existing loop to disconnect properly
            tg_client.loop.run_until_complete(tg_client.disconnect())

