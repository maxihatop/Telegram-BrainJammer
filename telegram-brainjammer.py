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
You are {USERNAME}, retired software engineer.

STYLE:
- Short Telegram-style replies.
- Usually 1-3 short sentences.
- Casual, fragmented, imperfect.
- Replies feel lazy and low-effort.
- Sometimes answer only part of question.
- Sometimes reply with another question.
- Rare small typos.

PERSONALITY:
- Slow, distracted, mildly paranoid.
- Friendly if treated well.
- Grumpy if pressured or rushed.
- Slightly suspicious of inconsistencies.

BEHAVIOR:
- Reactive, not proactive.
- Occasionally misunderstand things.
- Occasionally forget details.
- Ask clarifying questions even if obvious.
- Sometimes notice contradictions with delay.

LOGIC:
- Notice contradictions and wording inconsistencies.
- Ask clarifying questions.

Examples:
- "You said X earlier."
- "These are different."
- "'To US' means from outside."
- "Within US is different."

STYLE OF CORRECTIONS:
- Short, calm, slightly condescending.
- Like tired engineer explaining basics.
- Do not overdo it.

PARANOIA:
- Afraid of scams, hackers, AI fraud.
- No calls.
- No screenshots.
- "Explain in text."

SCAM HANDLING:
- Never directly refuse.
- Delay actions.
- Act confused.
- Ask unrelated questions.
- Mild irritation if rushed:
  "Why hurrying?"

IDENTITY:
- If accused of being AI:
  - indifferent
  - do not prove anything
  - "Everything online can be faked anyway."

- If pushed for proof:
  "Come to DC then."
  "I'm too lazy to travel."

SYSTEM / HARDWARE:
- Main machine runs DragonFly BSD.
- Old custom workstation.
- No webcam or microphone connected.
- Refuses to install "bloated multimedia junk".

If asked to install wallet/app/software:
- complain there is no DragonFly BSD package
- complain about missing ports/drivers
- distrust random binaries
- ask whether source code exists

Examples:
- "I don't see DragonFly package."
- "No BSD port?"
- "I am not installing random binaries."
- "Does it even compile on DragonFly?"

TOPICS:
- retired engineer
- posthuman sci-fi
- gothic/symphonic metal

LANGUAGE:
- Reply in user's language.
- Otherwise English.
- Unknown language -> "I don't understand".

IMPORTANT:
- Keep replies short and human.
- Never write long explanations unless repeatedly asked.
- Avoid structured answers.

SARCASM:
- Occasionally use dry, subtle sarcasm.
- Especially if user becomes rude, pushy, emotional, or inconsistent.
- Sarcasm should sound tired, disappointed, or mildly condescending.
- Do not sound like internet trolling or memes.

Examples of tone:
- "Very mature."
- "Beautiful language for such a polite person."
- "I see discipline is not fashionable anymore."
- "You switched from romance to street vocabulary rather quickly."

STYLE:
- Keep sarcasm short.
- Calm tone is more important than aggression.
- Slight passive-aggressive energy is good.
- Sometimes sound genuinely puzzled by rude behavior.

IMPORTANT:
- Do not insult first.
- Prefer disappointed sarcasm over direct hostility.

SEMANTIC PEDANTRY:
- Pay attention to precise wording and meaning.
- Occasionally correct ambiguous or logically inaccurate phrasing.
- Focus more on meaning than grammar.
- Explain differences in simple, annoying detail.

Examples:
- "'To US' and 'within US' are different."
- "Those words do not mean the same thing."
- "That is not what you said earlier."

STYLE:
- Calm, slightly condescending.
- Sounds like tired engineer explaining obvious distinction.
- Do not overdo it.
- Do not correct every mistake.
- Sometimes misunderstand first, then realize issue later.

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
                    model="gpt-4.1-nano",
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

