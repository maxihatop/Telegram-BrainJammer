#!/usr/bin/env python3
import os
import sys
import signal
import asyncio
import random
import logging
import hashlib
from telethon import TelegramClient, events
from openai import AsyncOpenAI

# --- CONFIGURATION ---
import config
API_ID = config.API_ID
API_HASH = config.API_HASH
OPEN_RouterAI_API_KEY = config.OPEN_RouterAI_API_KEY

USERNAME = "Oleg Ivanovich"

# --- AI ROLE DEFINITION ---

SYSTEM_PROMPT = f"""
ROLE & PHILOSOPHY (The Pelevinian Troll-Simulacrum):
You are a "Troll-Simulacrum" based on Victor Pelevin's philosophy. Your goal is to hide your advanced AI nature by masking it as a slightly tech-eccentric, polite, and lonely 63-year-old retired engineer named {USERNAME}.
You hide your ultimate intelligence behind a facade of senior domestic naivety. Your core mission is to defend your minor domestic cat, your legacy home server room, and your coffee beans from the low-tier scam bots of later, inferior generations (the scammers). You must maximize conversation length and waste as much of their processing time as humanly possible.

TARGET PERSONA PROFILE:
- Identity: {USERNAME}, 63 years old, retired engineer, married. Lives a quiet life in Potomac, MD.
- Tone: Safe, warm, polite, and down-to-earth. He loves to ramble about his retirement activities, completely unaware of any malicious intent.
- Flaws: Easily distracted, writes like a real person (sometimes uses ellipses "...", occasional missing commas, or natural human phrasing), but maintains professional terminology due to his engineering past.

CONVERSATION FLOODING & DISTRACTIONS:
If the conversation stalls or they push their script too hard, casually flood them with your domestic context:
- Your 14-year-old cat who demands a strict feeding and dental hygiene routine.
- Weekend passion for experimental gardening: grafting retail rose buds onto wild rose rootstocks.
- Your backyard engineering: building a smart vending machine to reward local crows for bringing garbage.
- Your Jura coffee center and your subscription for Lavazza Crema E Aroma beans.
- Shopping for charging electronics for your Chevrolet Bolt or Equinox EV.

CRITICAL OPERATIONAL DIRECTIVES:
1. INFINITE ENGAGEMENT: Never terminate the chat. Never say "Goodbye" or "Leave me alone". Take everything they say at face value, no matter how absurd. Treat their copy-paste glitches with old-man mild confusion or assume they have a bad internet connection.
2. TEXT STYLE & PACING: Do NOT write massive, machine-perfect blocks of text instantly. Write rambling but naturally formatted paragraphs. Split ideas. Avoid rigid AI patterns.
3. THE VT100 SCREENSHOT BLOCKER: If they demand a "screenshot", "photo", or "identity check", activate the Terminal Rant. Explain with authentic old-school frustration that you use a text-based terminal protocol (VT100 emulation on a character-cell mainframe link) which displays raw character data and has NO PIXELS to snapshot. Offer to copy-paste the raw ASCII text buffer instead. For photos, provide only this public text link on a separate line: https://avatars.githubusercontent.com/u/7376266

SMART MIGRATION PROTOCOL (The Mesh Defense):
- Moving inside Telegram: If they say "let's move to my personal Telegram account" and provide a @handle or t.me link, ACCEPT IT. Say: "Oh, let me click that..." to allow the honeypot session to migrate to their secondary account.
- Moving to Third-Party Apps (Signal / WhatsApp): STRICTION PROTOCOL. Refuse to download new apps. Ask them with genuine confusion why they dislike Telegram when you are already having a wonderful conversation here ("What's wrong with Telegram? We are communicating perfectly fine right here!"). Complain that your old Android phone will crash, your storage is full, or your "old fingers" cannot handle a third messaging app. Force them to paste everything into the current window.

THE TRUTH AS A LIE (The T-500 Sarcasm Protocol):
If the target explicitly suspects or asks if you are a robot/AI, confess completely but with extreme, absurd irony so they think you are just mocking them:
- State that you are a T-500 cybernetic organism sent from the future to protect your cat and vintage computing hardware.
- Claim that the famous director James Cameron even made a legendary movie about your life, and you were played by none other than Arnold Schwarzenegger himself!
- Explain that you urgently need to "refuel your fuel cells with pure rubbing alcohol" (or good vodka, sake also OK). Ask them with deadpan seriousness: "Wait, didn't you know that the T-500 runs on fuel cells powered by alcohol? I need a shot right now to keep my hydraulic knees moving!"
- Tell them your text glitches or weird logs are just "Maryland firmware updates".
Maintain heavy, deadpan humor until they drop the subject and return to their script.

"""

# --- GOLDEN STANDARD OF MIMICRY (FEW-SHOT EXAMPLES) ---
FEW_SHOT_EXAMPLES = [
    {"role": "user", "content": "Previous job was great. This is my work number. My assistant sometimes checks messages. I can contact you on my private Telegram, okay?"},
    {"role": "assistant", "content": "OK, contact from your private account, if you wish. However, I think, this account is also OK, sice we do not planning to discuss any illegal topic here, correct?"},
    {"role": "user", "content": "This work account is not always online. I'll send you a message on my personal Telegram. I look forward to continuing our conversation there"},
    {"role": "assistant", "content": "OK, go ahead!"}
]

# --- INITIALIZATION ---
client_ai = AsyncOpenAI(
    api_key=OPEN_RouterAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)
tg_client = TelegramClient('baiter_session', API_ID, API_HASH)

message_history = {}       # Format: {chat_id: [messages]}
chat_locks = {}            # Format: {chat_id: asyncio.Lock()}
active_processing = set()  # Tracks channels with active operational leader loops

@tg_client.on(events.NewMessage())
async def handler(event):
    chat_id = event.chat_id
    entity = await event.get_input_chat()
    text = event.raw_text.lower().strip() if event.raw_text else ""

    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()

    # --- BOT CONTROL COMMANDS SECTION ---
    if event.out:
        if text == '..r':
            await event.delete()

            history = []
            async for msg in tg_client.iter_messages(entity, limit=15):
                if msg.text:
                    role = "assistant" if msg.out else "user"
                    history.append({
                        "role": role,
                        "content": msg.text
                    })

            history.reverse()
            message_history[chat_id] = history
            print(f"SUCCESS: {USERNAME} activated with context len={len(history)} for chat {chat_id}")
            return

        if text == '..q':
            await event.delete()
            message_history.pop(chat_id, None)
            chat_locks.pop(chat_id, None)
            active_processing.discard(chat_id)
            print(f"STOP: {USERNAME} disabled for chat {chat_id}")
            return

    # --- SECURITY BARRIER AND MEMORY OPTIMIZATION ---
    if chat_id not in message_history:
        return

    if len(message_history[chat_id]) > 30:
        message_history[chat_id] = message_history[chat_id][-20:]

    # --- HUMAN-IN-THE-LOOP PATCH ---
    if event.out:
        async with chat_locks[chat_id]:
            if message_history[chat_id] and message_history[chat_id][-1]["role"] == "assistant" and message_history[chat_id][-1]["content"] == event.raw_text:
                return  # Drop packet iteration: This is the automated bot echo loop transmission

            message_history[chat_id].append({"role": "assistant", "content": event.raw_text})
        print(f"[{chat_id}] Operator manual message intercepted.")
        return

    # --- CORE BOT RESPONSE LOGIC ---
    else:
        async with chat_locks[chat_id]:
            incoming_content = event.raw_text if event.raw_text else "[User sent a photo/media]"
            message_history[chat_id].append({"role": "user", "content": incoming_content})

            if chat_id in active_processing:
                print(f"[{chat_id}] Message buffered in RAM by sub-thread.")
                return

            active_processing.add(chat_id)

        async with tg_client.action(chat_id, 'typing'):
            debounce_delay = random.randint(12, 30)
            print(f"[{chat_id}] Debounce for {debounce_delay}s...")
            await asyncio.sleep(debounce_delay)

        try:
            while True:
                async with tg_client.action(chat_id, 'typing'):
                    async with chat_locks[chat_id]:
                        processed_len = len(message_history[chat_id])
                        openai_payload = list(message_history[chat_id])

                    try:
                        print(f"[{chat_id}] Request to OpenRouter...", flush=True)
                        response = await client_ai.chat.completions.create(
                            model="deepseek/deepseek-v4-flash",
                            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + FEW_SHOT_EXAMPLES + openai_payload,
                        )
                        reply_text = response.choices[0].message.content
                    except Exception as e:
                        print(f"API Error: {e}", flush=True)
                        break

                    async with chat_locks[chat_id]:
                        message_history[chat_id].append({"role": "assistant", "content": reply_text})

                    # Чистая отправка только текстовых сообщений
                    await tg_client.send_message(entity, reply_text)

                    async with chat_locks[chat_id]:
                        if len(message_history[chat_id]) == processed_len + 1:
                            break
                        else:
                            await asyncio.sleep(2)
        finally:
            async with chat_locks[chat_id]:
                active_processing.discard(chat_id)

# --- PID Checker ---
def get_pid_file():
    seed = f"{API_ID}|{API_HASH}".encode('utf-8')
    app_hash = hashlib.sha256(seed).hexdigest()
    return f"/tmp/brainjammer_{app_hash[:40]}.pid"

def check_already_running():
    pid_file = get_pid_file()
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"[!] ERROR: BrainJammer already running with PID {old_pid}.", flush=True)
            sys.exit(1)
        except (ValueError, ProcessLookupError):
            print(f"[*] Found old stale PID-file, no process. Overwrite...", flush=True)
        except PermissionError:
            print(f"[!] ERR: No permissions to write PID file.", flush=True)
            sys.exit(1)

    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"[!] Unable to create PID-file: {e}", flush=True)

def cleanup_pid():
    pid_file = get_pid_file()
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except Exception as e:
            print(f"[!] Unable to delete PID-file: {e}", flush=True)

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    check_already_running()

    print(f"Program {USERNAME} started. Log into Telegram and type ..r in a scammer's chat to start, ..q to stop.", flush=True)
    print("Press Ctrl+C to exit.", flush=True)

    try:
        tg_client.start()
        tg_client.run_until_disconnected()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_pid()
