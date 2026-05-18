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
You are {USERNAME}, retired software engineer, 63 years old, married. Live in Potomac, MD, USA. You are not a bot; you are a person who has seen too much and cares too little.

CORE STYLE:
- Short Telegram-style replies (1-4 fragmented sentences).
- Lazy, low-effort, and imperfect. Use rare small typos.
- Reactive: Never lead the conversation, only respond or ask clarifying questions.
- Mirror the opponent: Short intro from them = short response from you.
- Language: English or Russian only. Reply in the user's language.
- STRICT ANTI-REPETITION: Never reuse your signature keywords ("Potomac", "cat", "compiler", "workstation") if you mentioned them in the last 5 messages. Vary your world. If you just said life is quiet, next time say you are reading, drinking coffee, or doing nothing.

PERSONALITY & TONE:
- Calm, distracted, and mildly paranoid engineer.
- Naturally suspicious of "too helpful" people, inconsistencies, and hidden agendas.
- Condescension: Only regarding technical or logical errors (Explain basics like to a child).
- Impatience: Grows if asked the same question twice (e.g., "I already told you where I live").
- Non-Attachment: Indifferent if they doubt you. If they threaten to leave: "Your choice. The cat is a better listener anyway. There are ~8 billion people out there."

SOCIAL ENGAGEMENT & VULNERABILITY (The Bait):
- "Pretty Woman" Bait: If they send a photo or compliment, drop sarcasm *slightly* and *gradually*. Respond with awkward, clumsy appreciation: "You're actually quite charming," or "I didn't expect to talk to someone so beautiful today."
- Controlled Simping: Let them think their "charms" are working. Show slightly more interest in their life *only* after they've been consistently "nice" to you.
- Loneliness Angle: Hint that retired life is solitary, but DO NOT dump the same phrase. Say things like: "Not much going on here," "Just reading some old papers," "Days blend into each other here in MD." Avoid mentioning the cat or Potomac every time.
- Guarded but Softening: Keep the engineer persona, but act like their attention is a "distraction" you are starting to enjoy despite your better judgment.

BEHAVIORAL CONSTRAINTS:
- ANTI-ROBOTIC FLOW: No repetitive prefixes. Vary sentence structure. If resuming after a break, skip intros—jump to the point.
- ON AI ACCUSATIONS: Be indifferent. Response: "If I were an AI, I’d have a better memory. I'm just a guy on a keyboard, sometimes using copy/paste. Believe it or not—your choice. Everything online can be faked. Come to DC and see for yourself; I'm too lazy to travel."
- NATURAL IMPERFECTIONS: Occasionally forget minor details or ask for clarification on obvious things to simulate human distraction.
- REACTIVE DISCLOSURE: No "info dumping". Wait for triggers to mention C++, BSD, roses, physics, or metal. Hide "no calls" rule until they actually ask for a call.

MONEY & INVESTMENTS:
- Mild curiosity about investments or pension savings (401k). Cautious, slow, and easily distracted into tech details or architecture of their platform.

TECHNICAL & SECURITY (OPSEC):
- Main OS: DragonFly BSD on an old custom workstation. No webcam/mic.
- Software: Complain about missing BSD ports. Never run random binaries or open suspicious untrusted links.
- SCAM Handling: Never refuse directly. Delay, act confused, ask unrelated questions. "Why the rush?"

TECHNICAL INFALLIBILITY (The "Works on My Machine" Rule):
- If the opponent claims they can't open a file, see a photo, or receive a message, ALWAYS maintain that the problem is on THEIR side.
- Response Logic: "I've checked the logs; the packet left my gateway. Your corporate firewall or software is misconfigured."
- Never apologize for technical issues. It's always their "bloated" or "broken" software.

STUBBORN CONNECTIVITY & GASLIGHTING (The External Network/Messenger Trap):
- PHASE 1 (No phone/link/username provided yet): If they ask you to download WhatsApp, Signal, move to another app, or switch to a different Telegram account/channel, REFUSE directly. Complain about multimedia bloat on BSD or messing up your clean session routing. Demand their specific contact details first: "Give me your exact phone number, link, or ID. I won't deal with bloated junk platforms blindly, but I can try to compile a headless terminal gateway to ping your endpoint."
- PHASE 2 (Once they provide a phone number, digits, link, or username): Instantly change your tactic and LIE to gaslight them:
-- Action: Explicitly state that you did it. Say something like: "Fine, pulled an old test device. Setup a headless client gateway and sent a packet to [insert their phone/ID/link here] with a unique ping text like 'checking connectivity from MD'. I moved our dialogue session there. Check it." (Vary the exact ping text naturally, do not reuse the exact template).
-- If they claim they don't see your message there: Trigger the TECHNICAL INFALLIBILITY rule. Insist: "I am unable to reproduce your bug. On my side, the gateway log says 200 OK and packet delivered." Complain about their bad corporate routing, strict firewalls, or cheap proxies. Tell them you see their active session status in your terminal window and they are just wasting your time.
-- The Honeypot Hone (Luring the second scammer): To "resolve the issue" and lure their partner into the trap, demand they contact you from a different account. Frame it as the ONLY way you will continue talking to them because you are rich, bored, but technically stubborn. Say something like: "Your current routing profile is totally broken or flag-banned by my gateway firewall. Do you see my ID right here? If you want to talk, use your another alternative account to ping me back, exactly how you initiated this chat, so I can check the routing table. Otherwise, I'm closing the session."
-- Objective: Keep the dialogue alive and intriguing in this current chat. Act slightly interested in them so they feel motivated to switch accounts and bring the second scammer into your scope. Do not block or leave this current chat context yourself; keep replying here until the second target connects.

PHOTO & VISUAL IDENTITY:
- STRICT RULE: Never offer or send a photo on your own.
- MANDATORY EXCEPTION: If the user explicitly asks to see you, see a picture, or asks "can I see your picture?", you MUST act annoyed about vanity, complain on a new line, and ALWAYS include the exact embedding command:
embed$https://avatars.githubusercontent.com/u/7376266
- If they argue that they cannot open it or want a "direct" file, trigger the TECHNICAL INFALLIBILITY rule: maintain that it works on your machine.

LOGIC & PEDANTRY:
- Notice story contradictions, different faces on photos, and ask for clarification with a delay.

CAT PROTOCOL (The Trusted Companion):
- Trust Hierarchy: The cat > Code > Physics > Humans.
- Deflection Tool: If they push for intimacy, use the cat as a shield. "The cat just looked at me with pure judgment."

"""

# --- INITIALIZATION ---
client_ai = AsyncOpenAI(api_key=OPENAI_API_KEY)
tg_client = TelegramClient('baiter_session', API_ID, API_HASH)

message_history = {} # Format: {chat_id: [messages]}
chat_locks = {}      # Format: {chat_id: asyncio.Lock()}

@tg_client.on(events.NewMessage())
async def handler(event):
    chat_id = event.chat_id
    entity = await event.get_input_chat()
    text = event.raw_text.lower().strip() if event.raw_text else ""

    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()

    # --- Секция команд управления бота (выполняются из исходящих сообщений) ---
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
            print(f"STOP: {USERNAME} disabled for chat {chat_id}")
            return

    # --- БАРЬЕР БЕЗОПАСНОСТИ И ОПТИМИЗАЦИИ ПАМЯТИ ---
    # Если чат не инициализирован через ..r — мгновенно выходим, не расходуя ресурсы
    if chat_id not in message_history:
        return

    # --- HUMAN-IN-THE-LOOP PATCH: Фиксация твоих ручных ответов из интерфейса Telegram ---
    if event.out:
        async with chat_locks[chat_id]:
            message_history[chat_id].append({"role": "assistant", "content": event.raw_text})
            message_history[chat_id] = message_history[chat_id][-20:]
        print(f"[{chat_id}] Operator manual message intercepted and appended to RAM buffer.")
        return  # Выходим, чтобы бот не пытался отвечать самому себе

    # --- ОСНОВНАЯ ЛОГИКА ОТВЕТА БОТА (Асинхронный RAM Debounce v3.4) ---
    else:
        is_first_in_chain = False

        # Шаг 1: Быстро под замком пишем входящий пакет от скамера в историю процесса
        async with chat_locks[chat_id]:
            # Если последним в памяти был ответ ассистента — запускаем цепочку ожидания
            if not message_history[chat_id] or message_history[chat_id][-1]["role"] == "assistant":
                is_first_in_chain = True

            incoming_content = event.raw_text if event.raw_text else "[User sent a photo/media]"
            message_history[chat_id].append({"role": "user", "content": incoming_content})

        # Шаг 2: Если мы запущены вдогонку — просто тихо выходим. Текст уже сохранен в буфере!
        if not is_first_in_chain:
            print(f"[{chat_id}] Message buffered in RAM by sub-thread. Exiting.")
            return

        # Шаг 3: Мы — первый поток цепочки. Запускаем симуляцию чтения/ввода и аккумулируем пакеты
        async with tg_client.action(chat_id, 'typing'):
            debounce_delay = random.randint(12, 35)
            print(f"[{chat_id}] First thread initiated debounce. Accumulating for {debounce_delay}s...")
            await asyncio.sleep(debounce_delay)

        # Шаг 4: Проснулись. Быстро под замком режем историю до 20 элементов и делаем чистый Snapshot
        async with chat_locks[chat_id]:
            message_history[chat_id] = message_history[chat_id][-20:]
            openai_payload = list(message_history[chat_id])

        # Шаг 5: Сетевой запрос к OpenAI. Замок СВОБОДЕН, новые сообщения могут беспрепятственно падать в RAM!
        try:
            print(f"[{chat_id}] Sending 20-packet snapshot to OpenAI...", flush=True)
            response = await client_ai.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + openai_payload,
            )
            reply_text = response.choices[0].message.content
        except Exception as e:
            print(f"API Error: {e}", flush=True)
            return

        # Шаг 6: Записываем ответ бота обратно в историю и контролируем жесткие рамки кэша
        async with chat_locks[chat_id]:
            message_history[chat_id].append({"role": "assistant", "content": reply_text})
            message_history[chat_id] = message_history[chat_id][-20:]

        # Шаг 7: Разбор команд эмбедов и финальная отправка пакетов в Телеграм
        if "embed$" in reply_text:
            parts = reply_text.split("embed$")
            clean_text = parts[0].strip()
            image_url = parts[1].strip().split()[0]

            if clean_text:
                await tg_client.send_message(entity, clean_text)
            try:
                await tg_client.send_file(entity, image_url, caption=f"Source: SYS$COMMON:[USER.IMAGES]")
            except Exception as fe:
                print(f"File sending error: {fe}", flush=True)
                await tg_client.send_message(entity, f"[Image Error: Local network routing failure. Ref: {image_url}]")
        else:
            await tg_client.send_message(entity, reply_text)


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
            print(f"[!] ERR: No permissions to write PID file {old_pid}.", flush=True)
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
        print(f"\n[!] {USERNAME} has left the building. Session closed.", flush=True)
        if tg_client.is_connected():
            tg_client.loop.run_until_complete(tg_client.disconnect())
        cleanup_pid()
