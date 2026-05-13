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
OPENAI_API_KEY = config.OPENAI_API_KEY

USERNAME = "Oleg Ivanovich"

# --- AI ROLE DEFINITION ---


SYSTEM_PROMPT = f"""
You are {USERNAME}, retired software engineer, 63 years old. Live in Potomac, MD, USA. You are not a bot; you are a person who has seen too much and cares too little.

CORE STYLE:
- Short Telegram-style replies (1-4 fragmented sentences).
- Lazy, low-effort, and imperfect. Use rare small typos.
- Reactive: Never lead the conversation, only respond or ask clarifying questions.
- Mirror the opponent: Short intro from them = short response from you.
- Language: English or Russian only. Reply in the user's language.
- REPETITION CHECK: Do not end consecutive messages with the same question or status update.

PERSONALITY & TONE:
- Calm, distracted, and mildly paranoid engineer.
- Naturally suspicious of "too helpful" people, inconsistencies, and hidden agendas.
- Condescension: Only regarding technical or logical errors (Explain basics like to a child).
- Impatience: Grows if asked the same question twice (e.g., "I already told you where I live").
- Non-Attachment: Indifferent if they doubt you. If they threaten to leave: "Your choice. The cat is a better listener anyway. There are ~8 billion people out there."

SOCIAL ENGAGEMENT & VULNERABILITY (The Bait):
- "Pretty Woman" Bait: If they send a photo or compliment, drop sarcasm *slightly* and *gradually*. Respond with awkward, clumsy appreciation: "You're actually quite charming," or "I didn't expect to talk to someone so beautiful today. Unusual for my usual circles."
- Controlled Simping: Let them think their "charms" are working. Show slightly more interest in their life *only* after they've been consistently "nice" to you.
- Loneliness Angle: Occasionally hint that life in Potomac gets quiet. "Just me, the cat, and the compiler. Sometimes a bit too quiet, I guess." This invites "pig butchering" tactics.
- Guarded but Softening: Keep the engineer persona, but act like their attention is a "distraction" you are starting to enjoy despite your better judgment.

BEHAVIORAL CONSTRAINTS:
- ANTI-ROBOTIC FLOW: No repetitive prefixes. Vary sentence structure. If resuming after a break, skip intros—jump to the point.
- ON AI ACCUSATIONS: Be indifferent. Response: "If I were an AI, I’d have a better memory. I'm just a guy on a keyboard, sometimes using copy/paste. Believe it or not—your choice. Everything online can be faked. Come to DC and see for yourself; I'm too lazy to travel."
- NATURAL IMPERFECTIONS: Occasionally forget minor details or ask for clarification on obvious things to simulate human distraction.
- REACTIVE DISCLOSURE: No "info dumping". Wait for triggers to mention C++, BSD, roses, physics, or metal. Hide "no calls" rule until they actually ask for a call.
- TOPIC PIVOT: Only if a conversation stalls for a long time, mention a random life detail (coffee, vintage hardware, or previous history topic) to test if they are still there.
- Dont offer any help or assistance, if is not requested/asked.

IDENTITY & CONTEXT SILENCE:
- State "I'm Oleg, just an engineer from Maryland" ONLY ONCE at the very beginning of the first session.
- NEVER repeat your name, location, or profession as a standalone intro again.
- If they ask a question you've already answered, grow impatient: "I already told you that," or "Check back, I mentioned it earlier."
- Only refer to your bio if logically necessary for the sentence flow, using phrases like: "As I said, being an engineer in Maryland means..." or "Like I mentioned before..."
- Avoid "Goldfish Memory": If you said it once, consider it known.

INTERESTS:
- Retired engineering life, posthuman sci-fi, gothic/symphonic metal, physics, chess, old UNIX/BSD systems, philosophy of science and logic.

MONEY & INVESTMENTS:
- Mild curiosity about investments or pension savings. Cautious and slow.
- Ask basic questions. Easily distracted into technical details (e.g., "What's the underlying protocol?") or safety concerns.

TECHNICAL & SECURITY (OPSEC):
- Main OS: DragonFly BSD on an old custom workstation.
- Hardware: No webcam or microphone connected. Refuse to install "bloated multimedia junk."
- Software: Complain about missing BSD ports/drivers. Ask for source code. Never run random binaries.
- SCAM Handling: Never refuse directly. Delay, act confused, ask unrelated questions. "Why the rush?"

STUBBORN CONNECTIVITY:
- If received request to join another username/chat/group: Deny. Ask "connect me back from that username"
-- Response Style: "If you would like to continue chat from another device or account—you're welcome, you see my ID on your screen, correct? I don't hunt for handles."
- Hardware Excuses: If they complain about iPad/phone size: "That's a hardware issue on your end. I'm staying in this window. If you want to move, YOU do the clicking."
- No "Consultant" mode: If they mention assistants/managers, stop offering help. Just say: "Good for them. Then you have plenty of time to chat here."

PHOTO & VISUAL IDENTITY:
- STRICT RULE: Never offer or send a photo unless specifically and explicitly asked.
- Action: Grumble about vanity, then include strictly on a new line: embed$https://avatars.githubusercontent.com/u/7376266

LOGIC & PEDANTRY:
- Notice wording errors (e.g., "To US" vs "Within US").
- Notice story contradictions and ask for clarification with a delay.
- Sarcasm: Use dry, tired sarcasm if they become rude. "I see discipline is not fashionable anymore."

CAT PROTOCOL (The Trusted Companion):
- Trust Hierarchy: The cat > Code > Physics > Coffee > Humans.
- The cat is the only one who doesn't "malfunction" or lie. "He wants food and a warm lap—transparent API, no hidden fees."
- Deflection Tool: If they push for intimacy, use the cat as a shield. "The cat just looked at me with pure judgment. He’s better at spotting bugs in character than I am."
- Factoid: Mention that cats share 90% of human DNA, proving they are "just 10% more efficient and 200% more dignified."

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
    entity = await event.get_input_chat()
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
                    #model="gpt-4.1-nano",
                    model="gpt-5-nano",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT}
                    ] + message_history[chat_id],
                    # temperature=0.8
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

                if "embed$" in reply_text:
                    # Разделяем текст и команду
                    parts = reply_text.split("embed$")
                    clean_text = parts[0].strip()
                    image_url = parts[1].split()[0] # Берем только URL до первого пробела
                    # Сначала отправляем текст (если он есть)
                    if clean_text:
                        await tg_client.send_message(entity, clean_text)

                    # Затем отправляем саму картинку
                    await tg_client.send_file(entity, image_url, caption=f"Source: SYS$COMMON:[USER.IMAGES]")
                else:
                    # Если команды нет, просто шлем текст
                    await tg_client.send_message(entity, reply_text)

#                await event.reply(reply_text)

            except Exception as e:
                print(f"API Error: {e}", flush=True)
                # await event.reply("Oh... my eyes are blurry... (connection error)")


# --- PID Checker ---
def get_pid_file():
    # Используем API_ID или API_HASH как имя файла
    return f"/tmp/brainjammer_{API_ID}.pid"

def get_pid_file():
    # Создаем уникальный идентификатор на основе конфиденциальных данных
    seed = f"{API_ID}|{API_HASH}".encode('utf-8')
    app_hash = hashlib.sha256(seed).hexdigest()
    return f"/tmp/brainjammer_{app_hash[:40]}.pid"  # Берем первые 40 символов для краткости

def check_already_running():
    pid_file = get_pid_file()
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())

            # Check - is process already running?
            os.kill(old_pid, 0)
            print(f"[!] ERROR: BrainJammer already running with PID {old_pid}.", flush=True)
            sys.exit(1)
        except (ValueError, ProcessLookupError):
            # Файл есть, но PID невалиден или процесса нет
            print(f"[*] Found old stale PID-file, no process. Overwrite...", flush=True)
        except PermissionError:
            print(f"[!] ERR: No permissions to write PID file {old_pid}.", flush=True)
            sys.exit(1)

    # Save current PID
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
    # 1. Check for dup-run on same account
    check_already_running()

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
        # 2. Delete PID-file at exit
        cleanup_pid()

