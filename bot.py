# -*- coding: utf-8 -*-
"""Bunker Telegram boti — asosiy fayl.

Ishga tushirish:  BOT_TOKEN=... python bot.py
Ixtiyoriy:        REDIS_URL=rediss://...  (Upstash)   PORT=10000 (Render beradi)
"""
import asyncio
import html
import logging
import os
import random
import re
import time

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiohttp import web

import data as D
import epilog as E
import game as G
import render as R
from storage import Storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bunker")

BOT: Bot = None
BOT_USERNAME = "bot"
STORE = Storage()
dp = Dispatcher()

GAMES = {}        # gid -> Game
USER_GAME = {}    # uid(str) -> gid  (faol o'yinlar)
CHAT_GAME = {}    # chat_id(str) -> gid (guruhdagi faol o'yin)
LOCKS = {}
EVENTS = {}
TASKS = {}
DIRTY = {}
LAST_REFRESH = {}
LAST_TEXT = {}
COOLDOWN = {}     # chat -> vaqt (flood himoyasi)


def esc(s):
    return html.escape(str(s), quote=False)


def lock(gid):
    if gid not in LOCKS:
        LOCKS[gid] = asyncio.Lock()
    return LOCKS[gid]


def event(gid):
    if gid not in EVENTS:
        EVENTS[gid] = asyncio.Event()
    return EVENTS[gid]


def poke(g, dirty=True):
    if dirty:
        DIRTY[g.id] = True
    event(g.id).set()


def clean_name(user, g=None):
    n = user.first_name or user.username or "O'yinchi"
    n = re.sub(r"[<>&\n]", "", n).strip()[:18] or "O'yinchi"
    if g:
        names = {p["name"] for p in g.all_players()}
        base, i = n, 2
        while n in names:
            n = f"{base} {i}"
            i += 1
    return n


# ======================================================== TELEGRAM I/O

async def send(chat, text, markup=None):
    for _ in range(2):
        try:
            m = await BOT.send_message(int(chat), text, reply_markup=markup)
            return m.message_id
        except TelegramRetryAfter as e:
            await asyncio.sleep(min(e.retry_after, 10) + 0.5)
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            log.info("send %s: %s", chat, e)
            return None
        except Exception as e:
            log.warning("send %s: %s", chat, e)
            return None
    return None


async def edit(chat, mid, text, markup=None):
    if not mid:
        return
    key = f"{chat}:{mid}"
    sig = text + (markup.model_dump_json() if markup else "")
    if LAST_TEXT.get(key) == sig:
        return
    if COOLDOWN.get(str(chat), 0) > time.time():
        return
    try:
        await BOT.edit_message_text(text, chat_id=int(chat), message_id=mid, reply_markup=markup)
        LAST_TEXT[key] = sig
    except TelegramRetryAfter as e:
        COOLDOWN[str(chat)] = time.time() + e.retry_after + 1
    except TelegramBadRequest as e:
        if "not modified" in str(e):
            LAST_TEXT[key] = sig
        else:
            log.info("edit %s: %s", chat, e)
    except Exception as e:
        log.warning("edit %s: %s", chat, e)


async def delete(chat, mid):
    if not mid:
        return
    try:
        await BOT.delete_message(int(chat), mid)
    except Exception:
        pass
    LAST_TEXT.pop(f"{chat}:{mid}", None)


async def answer(cb: CallbackQuery, text=None, alert=False, url=None):
    try:
        await cb.answer(text, show_alert=alert, url=url)
    except Exception:
        pass


def targets(g):
    return [g.chat_id] if g.mode == "group" else list(g.order)


async def broadcast(g, text, markup=None):
    for t in targets(g):
        await send(t, text, markup)


def dm_button():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🃏 Kartalarimga o'tish", url=f"https://t.me/{BOT_USERNAME}")]])


async def save(g):
    await STORE.save_game(g)


# ======================================================== XABARLARNI YANGILASH

async def refresh_lobby(g):
    text, markup = R.lobby(g, BOT_USERNAME)
    for chat, mid in g.msgs["lobby"]:
        await edit(chat, mid, text, markup)


async def post_board(g):
    for chat, mid in g.msgs["board"]:
        await delete(chat, mid)
    g.msgs["board"] = []
    text, markup = R.board(g), R.board_kb(g)
    for t in targets(g):
        mid = await send(t, text, markup)
        if mid:
            g.msgs["board"].append([t, mid])
            try:
                await BOT.pin_chat_message(int(t), mid, disable_notification=True)
            except Exception:
                pass


async def refresh_board(g):
    text, markup = R.board(g), R.board_kb(g)
    for chat, mid in g.msgs["board"]:
        await edit(chat, mid, text, markup)


async def post_cards(g, p):
    old = g.msgs["cards"].get(p["uid"])
    if old:
        await delete(p["uid"], old)
    mid = await send(p["uid"], R.cards(g, p), R.cards_kb(g, p))
    g.msgs["cards"][p["uid"]] = mid
    return mid


async def refresh_cards(g, p):
    mid = g.msgs["cards"].get(p["uid"])
    if mid:
        await edit(p["uid"], mid, R.cards(g, p), R.cards_kb(g, p))


async def refresh_all_cards(g):
    for p in g.all_players():
        await refresh_cards(g, p)


async def post_vote(g):
    g.vote_seq += 1
    g.votes = {}
    g.msgs["vote"] = []
    text = R.vote_text(g)
    if g.mode == "group":
        if g.settings["secret"]:
            mid = await send(g.chat_id, text, dm_button())
            g.msgs["vote"].append([g.chat_id, mid, None])
            for p in g.alive():
                mid = await send(p["uid"], text, R.vote_kb(g, p["uid"]))
                g.msgs["vote"].append([p["uid"], mid, p["uid"]])
        else:
            mid = await send(g.chat_id, text, R.vote_kb(g))
            g.msgs["vote"].append([g.chat_id, mid, "*"])
    else:
        for p in g.all_players():
            voter = p["uid"] if p["alive"] else None
            mid = await send(p["uid"], text, R.vote_kb(g, voter) if voter else None)
            g.msgs["vote"].append([p["uid"], mid, voter])


async def refresh_vote(g, final=False):
    text = R.vote_text(g, final)
    for chat, mid, voter in g.msgs["vote"]:
        if final:
            markup = None
        elif voter == "*":
            markup = R.vote_kb(g)
        elif voter:
            markup = R.vote_kb(g, voter)
        else:
            markup = dm_button() if g.mode == "group" else None
        await edit(chat, mid, text, markup)


async def refresh_live(g):
    await refresh_board(g)
    if g.phase in ("vote", "revote"):
        await refresh_vote(g)
    LAST_REFRESH[g.id] = time.time()
    DIRTY[g.id] = False


# ======================================================== O'YIN OQIMI

def set_phase(g, phase, seconds=None):
    g.phase = phase
    g.phase_started = time.time()
    g.deadline = time.time() + (seconds if seconds is not None else g.phase_time(phase))
    g.paused_left = None


async def start_game(g):
    G.deal(g)
    g.state = "play"
    n = len(g.order)
    for chat, mid in g.msgs["lobby"]:
        await edit(chat, mid, f"🏚 <b>BUNKER</b>\n\n✅ O'yin boshlandi · {n} o'yinchi · bunkerda {g.seats} joy", None)
    await broadcast(g, R.scenario(g))
    G.start_round(g)
    set_phase(g, "reveal")
    await broadcast(
        g,
        "🃏 <b>1-raund · Tanishuv</b>\n\nHammaning kasbi ochildi. Endi har kim shaxsiy xabarda "
        f"yana <b>bitta</b> kartasini tanlab ochadi. ⏱ {g.phase_time('reveal')} s",
        dm_button() if g.mode == "group" else None)
    await post_board(g)
    for p in g.alive():
        mid = await post_cards(g, p)
        if not mid and g.mode == "group":
            await send(g.chat_id, f"⚠️ {p['name']}, bot sizga yoza olmayapti. "
                                  f"Botni oching va Start bosing: @{BOT_USERNAME}")
    await save(g)
    TASKS[g.id] = asyncio.create_task(game_loop(g.id))


async def start_reveal(g):
    if g.remaining_kicks() <= 0:
        await finish(g)
        return
    set_phase(g, "reveal")
    n = g.reveals_needed()
    extra = ""
    if g.open2 and not g.settings.get("fast"):
        extra = "\n<i>«Hamma ochsin» kartasi tufayli bu raundda 2 tadan.</i>"
    left = g.remaining_kicks()
    await broadcast(
        g,
        f"🃏 <b>{g.round}-raund</b>\n\nHar kim shaxsiy xabarda <b>{n}</b> ta kartasini ochadi. "
        f"⏱ {g.phase_time('reveal')} s{extra}\n"
        f"<i>Bu raundda {g.kicks_round} kishi chiqadi · bunkerga hali {left} kishi ortiqcha.</i>",
        dm_button() if g.mode == "group" else None)
    for p in g.alive():
        await post_cards(g, p)
    poke(g)


async def end_reveal(g):
    auto = G.auto_reveal(g)
    auto_set = {(p["uid"], k) for p, k in auto}
    lines = [f"🃏 <b>{g.round}-raundda ochilgan kartalar</b>", ""]
    for p in g.alive():
        ks = g.round_reveals.get(p["uid"], [])
        if not ks:
            continue
        parts = []
        for k in ks:
            a = " <i>(avto)</i>" if (p["uid"], k) in auto_set else ""
            parts.append(f"{D.CARD_ICONS[k]} {p['cards'][k]['t']}{a}")
        lines.append(f"<b>{p['name']}</b>\n   " + "\n   ".join(parts))
    set_phase(g, "discuss")
    t = g.phase_time("discuss")
    if g.round == 1:
        lines.append(f"\n💬 <b>Tanishuv: {t} s.</b> O'zingizni tanishtiring — siz bunkerga nima olib kelasiz?")
    else:
        lines.append(f"\n💬 <b>Muhokama: {t} s.</b> Kim bunkerga loyiq, kim emas? Gapiring, isbotlang, blef qiling!")
    lines.append("<i>Hamma «Tayyorman» bossa, muhokama erta tugaydi.</i>")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tayyorman", callback_data=f"rd:{g.id}")],
        [InlineKeyboardButton(text="🃏 Mening kartalarim", callback_data=f"my:{g.id}")],
    ])
    await broadcast(g, "\n".join(lines), markup)
    await refresh_all_cards(g)


async def end_discuss(g):
    if g.round == 1:
        G.start_round(g)
        await start_reveal(g)
    else:
        await start_vote(g)


async def start_vote(g, revote=False):
    if not revote:
        g.tie = None
    set_phase(g, "revote" if revote else "vote")
    await post_vote(g)
    await refresh_all_cards(g)


async def end_vote(g):
    counts = G.tally(g)
    lead, top = G.leaders(g, counts)
    await refresh_vote(g, final=True)
    dice_text = ""
    if len(lead) > 1:
        if g.phase == "vote":
            g.tie = lead
            set_phase(g, "defense")
            names = ", ".join(f"<b>{g.players[u]['name']}</b>" for u in lead)
            await broadcast(
                g,
                f"⚖️ <b>Ovozlar teng!</b> {names}\n\nHar biringizga himoya so'zi uchun "
                f"{g.phase_time('defense')} s. Keyin faqat siz orangizda qayta ovoz beriladi.")
            return
        rolls = {}
        while True:
            rolls = {u: random.randint(1, 6) for u in lead}
            mn = min(rolls.values())
            if list(rolls.values()).count(mn) == 1:
                break
        kicked = min(rolls, key=rolls.get)
        dice_text = "🎲 <b>Yana teng! Zar tashlaymiz:</b>\n" + "\n".join(
            f"{g.players[u]['name']} — 🎲 {r}" for u, r in rolls.items()) + "\nEng kichik son chiqqan bunkerni tark etadi.\n\n"
    else:
        kicked = lead[0]
    G.kick(g, kicked, counts)
    g.tie = None
    p = g.players[kicked]
    p["lw_open"] = False
    p["lw_done"] = False
    g.lastword = kicked
    set_phase(g, "lastword")
    v = counts.get(kicked, 0)
    await broadcast(
        g,
        f"{dice_text}❌ <b>{p['name']}</b> bunkerdan chiqarildi ({v} ovoz).\n\n"
        f"🎤 Oxirgi so'z uchun {g.phase_time('lastword')} s. Xohlasa, yana bitta kartasini ochishi mumkin.")
    await post_cards(g, p)
    poke(g)


async def end_lastword(g):
    p = g.players.get(g.lastword) if g.lastword else None
    g.lastword = None
    if p:
        await refresh_cards(g, p)
    if len(g.alive()) <= g.seats:
        await finish(g)
        return
    if g.kicks_done < g.kicks_round and g.remaining_kicks() > 0:
        await broadcast(g, f"🔁 Bu raundda yana <b>{g.kicks_round - g.kicks_done}</b> kishi chiqishi kerak. Yangi ovoz!")
        await start_vote(g)
    else:
        G.start_round(g)
        await start_reveal(g)


async def advance(g):
    ph = g.phase
    if ph == "reveal":
        await end_reveal(g)
    elif ph == "discuss":
        await end_discuss(g)
    elif ph in ("vote", "revote"):
        await end_vote(g)
    elif ph == "defense":
        await start_vote(g, revote=True)
    elif ph == "lastword":
        await end_lastword(g)
    await save(g)


def phase_complete(g):
    ph = g.phase
    if ph == "reveal":
        return G.all_revealed(g)
    if ph == "discuss":
        return G.all_ready(g)
    if ph in ("vote", "revote"):
        return G.all_voted(g)
    if ph == "lastword":
        p = g.players.get(g.lastword)
        return bool(p and p.get("lw_done"))
    return False


async def game_loop(gid):
    ev = event(gid)
    while True:
        g = GAMES.get(gid)
        if not g or g.state != "play":
            return
        now = time.time()
        timeout = 15.0 if g.paused_left is not None else max(0.0, g.deadline - now)
        timeout = min(timeout, 15.0)
        if DIRTY.get(gid):
            timeout = min(timeout, max(0.0, 4.0 - (now - LAST_REFRESH.get(gid, 0))))
        try:
            await asyncio.wait_for(ev.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        ev.clear()
        async with lock(gid):
            g = GAMES.get(gid)
            if not g or g.state != "play":
                return
            try:
                now = time.time()
                if g.paused_left is None and (now >= g.deadline or phase_complete(g)):
                    await advance(g)
                    DIRTY[gid] = True
                if g.state != "play":
                    return
                since = time.time() - LAST_REFRESH.get(gid, 0)
                if (DIRTY.get(gid) and since >= 4) or since >= 15:
                    await refresh_live(g)
            except Exception:
                log.exception("game_loop %s", gid)
                await asyncio.sleep(2)


async def finish(g):
    g.state = "done"
    g.phase = "final"
    g.deadline = None
    ev = E.evaluate(g)
    g.result = ev["score"]
    names = ", ".join(f"<b>{p['name']}</b>" for p in g.alive())
    await broadcast(g, f"🏁 <b>O'YIN TUGADI!</b>\n\nBunkerga kirganlar: {names}\n\nEndi bilib olamiz — ular omon qoldimi?..")
    await asyncio.sleep(2)
    story = E.story(g, ev)
    for chunk in split_text(story):
        await broadcast(g, chunk)
    tail = E.outside_story(g, ev["score"])
    m = E.mvp(g)
    if m:
        tail += f"\n\n🏆 <b>O'yin MVPsi:</b> {esc(m['name'])} — eng kam ovoz olib bunkerga kirdi."
    await broadcast(g, tail.strip(), R.final_kb(g))
    await refresh_board(g)
    for p in g.all_players():
        try:
            await STORE.add_stats(p["uid"], p["name"], 1, 1 if p["alive"] else 0,
                                  1 if (p["alive"] and ev["score"] >= 60) else 0)
        except Exception:
            pass
    if g.mode == "group":
        for chat, mid in g.msgs["board"]:
            try:
                await BOT.unpin_chat_message(int(chat), message_id=mid)
            except Exception:
                pass
    await cleanup(g, keep=True)


def split_text(text, limit=3900):
    out, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 > limit and cur:
            out.append(cur)
            cur = para
        else:
            cur = (cur + "\n\n" + para) if cur else para
    if cur:
        out.append(cur)
    return out


async def cleanup(g, keep=False):
    for u, gid in list(USER_GAME.items()):
        if gid == g.id:
            USER_GAME.pop(u, None)
    if g.chat_id and CHAT_GAME.get(str(g.chat_id)) == g.id:
        CHAT_GAME.pop(str(g.chat_id), None)
    await STORE.delete_game(g.id)
    if not keep:
        GAMES.pop(g.id, None)
    else:
        g.state = "done"


async def stop_game(g, by_name):
    was_play = g.state == "play"
    g.state = "done"
    poke(g, False)
    text = f"⛔ O'yin to'xtatildi ({esc(by_name)})."
    if was_play:
        await broadcast(g, text)
        if g.mode == "group":
            for chat, mid in g.msgs["board"]:
                try:
                    await BOT.unpin_chat_message(int(chat), message_id=mid)
                except Exception:
                    pass
    else:
        for chat, mid in g.msgs["lobby"]:
            await edit(chat, mid, "🏚 <b>BUNKER</b>\n\n" + text, None)
    await cleanup(g)


# ======================================================== LOBBY AMALLARI

def active_game_of(uid):
    gid = USER_GAME.get(str(uid))
    g = GAMES.get(gid) if gid else None
    if g and g.state in ("lobby", "play"):
        return g
    return None


async def join(g, user, notify=True):
    """O'yinchini qo'shadi. Qaytaradi: (ok, xabar)."""
    uid = str(user.id)
    if g.state != "lobby":
        return False, "O'yin allaqachon boshlangan."
    other = active_game_of(uid)
    if other and other.id != g.id:
        return False, "Siz boshqa o'yindasiz. Avval undan chiqing: /chiqish"
    if uid in g.players:
        return False, "Siz allaqachon o'yindasiz ✓"
    if len(g.order) >= G.MAX_PLAYERS:
        return False, "O'yin to'lgan (14/14)."
    if g.mode == "group" and notify:
        mid = await send(uid, f"✅ Siz <b>Bunker</b> o'yiniga qo'shildingiz!\n\nO'yin boshlanganda kartalaringiz shu yerga keladi.")
        if not mid:
            return False, "dm"
    g.add_player(uid, clean_name(user, g))
    USER_GAME[uid] = g.id
    if g.mode == "room":
        text, markup = R.lobby(g, BOT_USERNAME)
        mid = await send(uid, text, markup)
        if mid:
            g.msgs["lobby"].append([uid, mid])
        name = g.players[uid]["name"]
        for p in g.all_players():
            if p["uid"] != uid:
                await send(p["uid"], f"➕ <b>{name}</b> xonaga qo'shildi.")
    await refresh_lobby(g)
    await save(g)
    return True, "Qo'shildingiz ✓"


async def leave_lobby(g, uid):
    uid = str(uid)
    if uid not in g.players:
        return
    name = g.players[uid]["name"]
    g.remove_player(uid)
    USER_GAME.pop(uid, None)
    if g.mode == "room":
        for row in list(g.msgs["lobby"]):
            if str(row[0]) == uid:
                await edit(row[0], row[1], "🏚 Siz xonadan chiqdingiz.", None)
                g.msgs["lobby"].remove(row)
        for p in g.all_players():
            await send(p["uid"], f"➖ {name} xonadan chiqdi.")
        if not g.order:
            await cleanup(g)
            return
    await refresh_lobby(g)
    await save(g)


async def create_group_game(chat_id, user):
    g = G.Game(mode="group", chat_id=str(chat_id))
    GAMES[g.id] = g
    CHAT_GAME[str(chat_id)] = g.id
    ok, msg = await join(g, user)
    if ok:
        g.host = str(user.id)
    text, markup = R.lobby(g, BOT_USERNAME)
    mid = await send(chat_id, text, markup)
    g.msgs["lobby"].append([str(chat_id), mid])
    if not ok and msg == "dm":
        await send(chat_id, f"ℹ️ Kartalar shaxsiy xabarda keladi. Qo'shilish uchun avval botni oching: "
                            f"https://t.me/{BOT_USERNAME}?start=j{g.id}")
    await save(g)
    return g


async def create_room(user):
    g = G.Game(mode="room")
    GAMES[g.id] = g
    await join(g, user, notify=False)
    g.host = str(user.id)
    await refresh_lobby(g)
    await save(g)
    return g


# ======================================================== BUYRUQLAR

@dp.message(CommandStart())
async def cmd_start(m: Message, command: CommandObject):
    if m.chat.type != ChatType.PRIVATE:
        await m.answer("Yangi o'yin uchun /bunker yozing.")
        return
    arg = command.args or ""
    if arg.startswith("j"):
        g = GAMES.get(arg[1:])
        if not g or g.state != "lobby":
            await m.answer("😕 Bu o'yin topilmadi yoki allaqachon boshlangan.")
            return
        async with lock(g.id):
            ok, msg = await join(g, m.from_user)
        if not ok:
            await m.answer(msg if msg != "dm" else "Xatolik. Qayta urinib ko'ring.")
        return
    text, markup = R.welcome(BOT_USERNAME)
    await m.answer(text, reply_markup=markup)


@dp.message(Command("bunker", "yangi", "new"))
async def cmd_bunker(m: Message):
    if m.chat.type == ChatType.PRIVATE:
        g = active_game_of(m.from_user.id)
        if g:
            await m.answer("Siz allaqachon o'yindasiz. Chiqish: /chiqish")
            return
        await create_room(m.from_user)
        return
    gid = CHAT_GAME.get(str(m.chat.id))
    g = GAMES.get(gid) if gid else None
    if g and g.state in ("lobby", "play"):
        await m.reply("Bu guruhda o'yin allaqachon bor. To'xtatish: /stop")
        return
    other = active_game_of(m.from_user.id)
    if other:
        await m.reply("Siz boshqa o'yindasiz. Avval undan chiqing: /chiqish")
        return
    await create_group_game(m.chat.id, m.from_user)


@dp.message(Command("stop"))
async def cmd_stop(m: Message):
    uid = str(m.from_user.id)
    if m.chat.type == ChatType.PRIVATE:
        g = active_game_of(uid)
        if not g or g.mode != "room":
            await m.answer("To'xtatiladigan o'yin yo'q.")
            return
        if g.host != uid:
            await m.answer("Faqat xost o'yinni to'xtata oladi. O'zingiz chiqish uchun: /chiqish")
            return
    else:
        gid = CHAT_GAME.get(str(m.chat.id))
        g = GAMES.get(gid) if gid else None
        if not g:
            await m.reply("Bu guruhda faol o'yin yo'q.")
            return
        allowed = g.host == uid
        if not allowed:
            try:
                mem = await BOT.get_chat_member(m.chat.id, m.from_user.id)
                allowed = mem.status in ("creator", "administrator")
            except Exception:
                pass
        if not allowed:
            await m.reply("Faqat xost yoki guruh admini to'xtata oladi.")
            return
    async with lock(g.id):
        await stop_game(g, m.from_user.first_name or "")


@dp.message(Command("chiqish", "leave"))
async def cmd_leave(m: Message):
    uid = str(m.from_user.id)
    g = active_game_of(uid)
    if not g:
        await m.answer("Siz hech qaysi o'yinda emassiz.")
        return
    async with lock(g.id):
        if g.state == "lobby":
            await leave_lobby(g, uid)
            await m.answer("Siz o'yindan chiqdingiz.")
            return
        p = g.p(uid)
        USER_GAME.pop(uid, None)
        if p and p["alive"]:
            p["alive"] = False
            p["out_round"] = g.round
            g.history.append({"round": g.round, "uid": uid, "votes": 0, "left": True})
            await broadcast(g, f"🚶 <b>{p['name']}</b> o'yinni tark etdi va bunkerdan voz kechdi.")
            if g.host == uid and g.alive():
                g.host = g.alive()[0]["uid"]
            if len(g.alive()) <= g.seats:
                await finish(g)
            else:
                poke(g)
        await m.answer("Siz o'yindan chiqdingiz.")
        await save(g)


@dp.message(Command("qoidalar", "rules", "help"))
async def cmd_rules(m: Message):
    await m.answer(D.RULES_TEXT)


@dp.message(Command("kartalarim", "cards"))
async def cmd_cards(m: Message):
    g = active_game_of(m.from_user.id)
    if not g or g.state != "play":
        await m.answer("Hozir faol o'yiningiz yo'q.")
        return
    p = g.p(m.from_user.id)
    async with lock(g.id):
        mid = await post_cards(g, p)
    if not mid and m.chat.type != ChatType.PRIVATE:
        await m.reply(f"Botni shaxsiyda oching: @{BOT_USERNAME}")


async def profile_text(user):
    s = await STORE.get_stats(user.id) or {}
    played = s.get("played", 0)
    if not played:
        return "👤 <b>Profil</b>\n\nHali o'ynamagansiz. Birinchi o'yinni boshlang: /bunker"
    b = s.get("bunker", 0)
    sv = s.get("survived", 0)
    pct = round(b * 100 / played) if played else 0
    return (f"👤 <b>Profil · {esc(user.first_name or '')}</b>\n\n"
            f"🎮 O'yinlar: <b>{played}</b>\n"
            f"🏚 Bunkerga kirgan: <b>{b}</b> ({pct}%)\n"
            f"🌱 Jamoasi omon qolgan: <b>{sv}</b>")


@dp.message(Command("profil", "profile"))
async def cmd_profile(m: Message):
    await m.answer(await profile_text(m.from_user))


@dp.message(Command("top"))
async def cmd_top(m: Message):
    rows = await STORE.top(10)
    if not rows:
        await m.answer("🏆 Reyting hali bo'sh. Birinchi bo'ling: /bunker")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Eng ko'p bunkerga kirganlar</b>", ""]
    for i, (name, sc) in enumerate(rows):
        lines.append(f"{medals[i] if i < 3 else str(i + 1) + '.'} {esc(name)} — {sc}")
    await m.answer("\n".join(lines))


# ======================================================== XONA REJIMIDA CHAT

@dp.message(F.chat.type == ChatType.PRIVATE, F.text, ~F.text.startswith("/"))
async def room_chat(m: Message):
    g = active_game_of(m.from_user.id)
    if not g or g.mode != "room":
        if not g:
            await m.answer("O'yin boshlash uchun /bunker yozing yoki /start ni bosing.")
        return
    p = g.p(m.from_user.id)
    if not p:
        return
    icon = "💬" if p["alive"] else "🌫"
    text = f"{icon} <b>{p['name']}</b>: {esc(m.text[:1000])}"
    for q in g.all_players():
        if q["uid"] != p["uid"]:
            await send(q["uid"], text)


@dp.message(F.chat.type == ChatType.PRIVATE, ~F.text)
async def room_media(m: Message):
    g = active_game_of(m.from_user.id)
    if g and g.mode == "room":
        await m.answer("Hozircha xonada faqat matnli xabarlar uzatiladi.")


# ======================================================== CALLBACKLAR

def parse(cb):
    parts = cb.data.split(":")
    g = GAMES.get(parts[1]) if len(parts) > 1 else None
    return parts, g


@dp.callback_query(F.data.startswith("m:"))
async def cb_menu(cb: CallbackQuery):
    what = cb.data[2:]
    if what == "new":
        if active_game_of(cb.from_user.id):
            await answer(cb, "Siz allaqachon o'yindasiz. /chiqish", alert=True)
            return
        await answer(cb)
        await create_room(cb.from_user)
    elif what == "rules":
        await answer(cb)
        await send(cb.from_user.id, D.RULES_TEXT)
    elif what == "profile":
        await answer(cb)
        await send(cb.from_user.id, await profile_text(cb.from_user))


@dp.callback_query(F.data.startswith("j:"))
async def cb_join(cb: CallbackQuery):
    _, g = parse(cb)
    if not g:
        await answer(cb, "O'yin topilmadi.", alert=True)
        return
    async with lock(g.id):
        ok, msg = await join(g, cb.from_user)
    if msg == "dm":
        await answer(cb, url=f"https://t.me/{BOT_USERNAME}?start=j{g.id}")
        return
    await answer(cb, msg, alert=not ok and "allaqachon" not in msg)


@dp.callback_query(F.data.startswith("lv:"))
async def cb_leave(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or g.state != "lobby":
        await answer(cb)
        return
    if str(cb.from_user.id) not in g.players:
        await answer(cb, "Siz bu o'yinda emassiz.")
        return
    async with lock(g.id):
        await leave_lobby(g, cb.from_user.id)
    await answer(cb, "Chiqdingiz.")


@dp.callback_query(F.data.startswith("cl:"))
async def cb_close(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or g.state != "lobby":
        await answer(cb)
        return
    if g.host != str(cb.from_user.id):
        await answer(cb, "Faqat xost xonani yopa oladi.", alert=True)
        return
    async with lock(g.id):
        await stop_game(g, cb.from_user.first_name or "")
    await answer(cb, "Xona yopildi.")


@dp.callback_query(F.data.startswith("st:"))
async def cb_startgame(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or g.state != "lobby":
        await answer(cb)
        return
    if g.host != str(cb.from_user.id):
        await answer(cb, "O'yinni faqat xost (👑) boshlay oladi.", alert=True)
        return
    if len(g.order) < G.MIN_PLAYERS:
        await answer(cb, f"Kamida {G.MIN_PLAYERS} kishi kerak. Hozir: {len(g.order)}.", alert=True)
        return
    await answer(cb, "Boshladik! 🚀")
    async with lock(g.id):
        if g.state == "lobby":
            await start_game(g)


@dp.callback_query(F.data.startswith("set:"))
async def cb_settings(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or g.state != "lobby":
        await answer(cb)
        return
    if g.host != str(cb.from_user.id):
        await answer(cb, "Sozlamalarni faqat xost o'zgartira oladi.", alert=True)
        return
    text, markup = R.settings(g)
    old = g.msgs.get("settings")
    if old:
        await delete(old[0], old[1])
    mid = await send(cb.from_user.id, text, markup)
    if not mid:
        await answer(cb, url=f"https://t.me/{BOT_USERNAME}?start=go")
        return
    g.msgs["settings"] = [str(cb.from_user.id), mid]
    await answer(cb, "Sozlamalar shaxsiy xabarda ⚙️" if g.mode == "group" else None)


CYCLES = {"discuss": [60, 90, 120, 180], "reveal": [30, 45, 60]}


@dp.callback_query(F.data.startswith("sg:"))
async def cb_setting_toggle(cb: CallbackQuery):
    parts, g = parse(cb)
    if not g or g.state != "lobby" or g.host != str(cb.from_user.id):
        await answer(cb, "Sozlamalarni hozir o'zgartirib bo'lmaydi.")
        return
    key = parts[2]
    async with lock(g.id):
        if key in CYCLES:
            vals = CYCLES[key]
            cur = g.settings[key]
            g.settings[key] = vals[(vals.index(cur) + 1) % len(vals)] if cur in vals else vals[0]
        else:
            g.settings[key] = not g.settings[key]
        text, markup = R.settings(g)
        await edit(cb.message.chat.id, cb.message.message_id, text, markup)
        await refresh_lobby(g)
        await save(g)
    await answer(cb)


@dp.callback_query(F.data.startswith("sgx:"))
async def cb_setting_done(cb: CallbackQuery):
    await answer(cb, "Saqlandi ✓")
    await delete(cb.message.chat.id, cb.message.message_id)


@dp.callback_query(F.data.startswith("rv:"))
async def cb_reveal(cb: CallbackQuery):
    parts, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    async with lock(g.id):
        p = g.p(cb.from_user.id)
        if not p or not p["alive"] or g.phase != "reveal":
            await answer(cb, "Hozir karta ochish vaqti emas.")
            return
        if g.need_more(p) <= 0:
            await answer(cb, "Bu raund uchun yetarli karta ochdingiz ✓")
            return
        kind = parts[2]
        if not G.open_card(g, p, kind):
            await answer(cb, "Bu karta allaqachon ochiq.")
            return
        await refresh_cards(g, p)
        await save(g)
        poke(g)
    await answer(cb, f"Ochildi: {D.CARD_LABELS[kind]} ✓")


@dp.callback_query(F.data.startswith("rd:"))
async def cb_ready(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    async with lock(g.id):
        p = g.p(cb.from_user.id)
        if not p or not p["alive"]:
            await answer(cb, "Siz bu o'yinda faol emassiz.")
            return
        if g.phase != "discuss":
            await answer(cb, "Hozir muhokama vaqti emas.")
            return
        p["ready"] = not p["ready"]
        poke(g)
        ready = sum(1 for x in g.alive() if x["ready"])
        await answer(cb, (f"Tayyor ✓ ({ready}/{len(g.alive())})" if p["ready"] else "Tayyor bekor qilindi"))


@dp.callback_query(F.data.startswith("v:"))
async def cb_vote(cb: CallbackQuery):
    parts, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    async with lock(g.id):
        voter = g.p(cb.from_user.id)
        if g.phase not in ("vote", "revote") or str(g.vote_seq) != parts[2]:
            await answer(cb, "Bu ovoz berish tugagan.")
            return
        if not voter or not voter["alive"]:
            await answer(cb, "Faqat bunkerdagi o'yinchilar ovoz beradi.")
            return
        target = parts[3]
        if target == voter["uid"]:
            await answer(cb, "O'zingizga ovoz berib bo'lmaydi 🙂")
            return
        if target not in [c["uid"] for c in G.candidates(g)]:
            await answer(cb, "Bu o'yinchiga ovoz berib bo'lmaydi.")
            return
        changed = voter["uid"] in g.votes
        g.votes[voter["uid"]] = target
        poke(g)
        tname = g.players[target]["name"]
    await answer(cb, f"{'Ovoz o' + chr(39) + 'zgartirildi' if changed else 'Ovozingiz'}: {tname}")


@dp.callback_query(F.data.startswith("my:"))
async def cb_mycards(cb: CallbackQuery):
    _, g = parse(cb)
    if not g:
        await answer(cb)
        return
    p = g.p(cb.from_user.id)
    if not p:
        await answer(cb, "Siz bu o'yinda emassiz.", alert=True)
        return
    async with lock(g.id):
        mid = await post_cards(g, p)
    if not mid:
        await answer(cb, url=f"https://t.me/{BOT_USERNAME}?start=go")
    else:
        await answer(cb, "Kartalaringiz shaxsiy xabarda 🃏" if cb.message.chat.type != ChatType.PRIVATE else None)


@dp.callback_query(F.data.startswith("ac:"))
async def cb_action(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    p = g.p(cb.from_user.id)
    if not p or not p["alive"] or not p.get("action") or p["action_used"]:
        await answer(cb, "Maxsus kartani hozir ishlatib bo'lmaydi.")
        return
    text, markup = R.action_targets(g, p)
    await send(p["uid"], text, markup)
    await answer(cb)


@dp.callback_query(F.data.startswith("atx:"))
async def cb_action_cancel(cb: CallbackQuery):
    await answer(cb, "Bekor qilindi")
    await delete(cb.message.chat.id, cb.message.message_id)


@dp.callback_query(F.data.startswith("at:"))
async def cb_action_target(cb: CallbackQuery):
    parts, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    async with lock(g.id):
        p = g.p(cb.from_user.id)
        if (not p or not p["alive"] or not p.get("action") or p["action_used"]
                or g.phase not in ("reveal", "discuss", "vote", "defense", "revote")):
            await answer(cb, "Maxsus kartani hozir ishlatib bo'lmaydi.", alert=True)
            return
        target = None if parts[2] == "-" else parts[2]
        if target and (target not in g.players or not g.players[target]["alive"]):
            await answer(cb, "Bu o'yinchi tashqarida.", alert=True)
            return
        pub, priv = G.use_action(g, p, target)
        if pub is None:
            await answer(cb, priv, alert=True)
            return
        await delete(cb.message.chat.id, cb.message.message_id)
        await broadcast(g, pub)
        if priv:
            await send(p["uid"], priv)
        await refresh_all_cards(g)
        await save(g)
        poke(g)
    await answer(cb, "Ishlatildi ✨")


@dp.callback_query(F.data.startswith("h:"))
async def cb_host(cb: CallbackQuery):
    parts, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    if g.host != str(cb.from_user.id):
        await answer(cb, "Bu tugmalar faqat xost uchun.", alert=True)
        return
    cmd = parts[2]
    async with lock(g.id):
        now = time.time()
        if cmd == "pause":
            if g.paused_left is None:
                g.paused_left = max(5, g.deadline - now)
                await broadcast(g, "⏸ Xost o'yinni pauza qildi.")
                msg = "Pauza"
            else:
                g.deadline = now + g.paused_left
                g.paused_left = None
                await broadcast(g, "▶️ O'yin davom etmoqda!")
                msg = "Davom"
        elif cmd == "plus":
            if g.paused_left is not None:
                g.paused_left += 30
            else:
                g.deadline += 30
            msg = "+30 soniya"
        else:
            if g.paused_left is not None:
                g.paused_left = None
            g.deadline = now
            msg = "O'tkazildi"
        await refresh_cards(g, g.p(cb.from_user.id))
        await save(g)
        poke(g)
    await answer(cb, msg)


@dp.callback_query(F.data.startswith("lw:"))
async def cb_lastword_card(cb: CallbackQuery):
    parts, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    async with lock(g.id):
        p = g.p(cb.from_user.id)
        if not p or g.phase != "lastword" or g.lastword != p["uid"] or p.get("lw_open"):
            await answer(cb, "Endi karta ochib bo'lmaydi.")
            return
        kind = parts[2]
        if kind not in g.closed(p):
            await answer(cb)
            return
        p["opened"].append(kind)
        p["lw_open"] = True
        await broadcast(g, f"🎤 <b>{p['name']}</b> oxirgi kartasini ochdi:\n"
                           f"{D.CARD_ICONS[kind]} {D.CARD_LABELS[kind]}: <b>{p['cards'][kind]['t']}</b>")
        await refresh_cards(g, p)
        await save(g)
        poke(g)
    await answer(cb, "Ochildi")


@dp.callback_query(F.data.startswith("lwd:"))
async def cb_lastword_done(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or g.state != "play":
        await answer(cb)
        return
    async with lock(g.id):
        p = g.p(cb.from_user.id)
        if p and g.lastword == p["uid"]:
            p["lw_done"] = True
            poke(g)
    await answer(cb, "Rahmat!")


@dp.callback_query(F.data.startswith("fc:"))
async def cb_final_cards(cb: CallbackQuery):
    _, g = parse(cb)
    if not g or not g.players:
        await answer(cb, "Bu o'yin ma'lumotlari endi mavjud emas.", alert=True)
        return
    await answer(cb)
    for chunk in split_text(R.all_cards(g)):
        await send(cb.message.chat.id, chunk)


@dp.callback_query(F.data.startswith("again:"))
async def cb_again(cb: CallbackQuery):
    _, old = parse(cb)
    if not old:
        await answer(cb, "Yangi o'yin: /bunker", alert=True)
        return
    uid = str(cb.from_user.id)
    if active_game_of(uid):
        await answer(cb, "Siz allaqachon yangi o'yindasiz ✓")
        return
    if old.mode == "group":
        gid = CHAT_GAME.get(str(old.chat_id))
        if gid and GAMES.get(gid) and GAMES[gid].state in ("lobby", "play"):
            await answer(cb, "Yangi o'yin allaqachon ochilgan — lobbyga qo'shiling 👆")
            return
        await answer(cb, "Yangi lobby ochildi!")
        g = G.Game(mode="group", chat_id=str(old.chat_id))
    else:
        await answer(cb, "Yangi xona ochildi!")
        g = G.Game(mode="room")
    GAMES[g.id] = g
    if g.mode == "group":
        CHAT_GAME[str(g.chat_id)] = g.id
    g.settings = dict(old.settings)
    async with lock(g.id):
        # oldingi tarkibni qo'shamiz (bosgan kishi — xost)
        order = [uid] + [u for u in old.order if u != uid]
        for u in order:
            if active_game_of(u) or u not in old.players and u != uid:
                continue
            name = old.players[u]["name"] if u in old.players else clean_name(cb.from_user, g)
            g.add_player(u, name)
            USER_GAME[u] = g.id
        g.host = uid if uid in g.players else (g.order[0] if g.order else None)
        text, markup = R.lobby(g, BOT_USERNAME)
        if g.mode == "group":
            mid = await send(g.chat_id, text, markup)
            g.msgs["lobby"].append([g.chat_id, mid])
        else:
            for u in g.order:
                mid = await send(u, text, markup)
                if mid:
                    g.msgs["lobby"].append([u, mid])
        await save(g)


# ======================================================== ISHGA TUSHIRISH

async def restore():
    for d in await STORE.load_games():
        try:
            g = G.Game.from_dict(d)
        except Exception:
            continue
        if g.state not in ("lobby", "play"):
            continue
        GAMES[g.id] = g
        for u in g.order:
            if g.state == "lobby" or g.players[u]["alive"]:
                USER_GAME[u] = g.id
        if g.chat_id:
            CHAT_GAME[str(g.chat_id)] = g.id
        if g.state == "play":
            TASKS[g.id] = asyncio.create_task(game_loop(g.id))
        log.info("Tiklandi: %s (%s)", g.id, g.state)


async def prune():
    while True:
        await asyncio.sleep(1800)
        now = time.time()
        for gid, g in list(GAMES.items()):
            if g.state == "done" and now - g.created > 6 * 3600:
                GAMES.pop(gid, None)
            elif g.state == "lobby" and now - g.created > 3 * 3600:
                async with lock(gid):
                    await stop_game(g, "vaqt tugadi")


async def health_server():
    app = web.Application()

    async def ok(_):
        active = sum(1 for g in GAMES.values() if g.state == "play")
        return web.Response(text=f"Bunker bot ishlayapti. Faol o'yinlar: {active}")

    app.router.add_get("/", ok)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info("Health server :%s", port)


async def main():
    global BOT, BOT_USERNAME
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN topilmadi")
    BOT = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True))
    me = await BOT.get_me()
    BOT_USERNAME = me.username
    await BOT.set_my_commands([
        BotCommand(command="bunker", description="Yangi o'yin"),
        BotCommand(command="qoidalar", description="Qisqa qoidalar"),
        BotCommand(command="kartalarim", description="Kartalarimni ko'rsatish"),
        BotCommand(command="profil", description="Statistikam"),
        BotCommand(command="top", description="Reyting"),
        BotCommand(command="chiqish", description="O'yindan chiqish"),
        BotCommand(command="stop", description="O'yinni to'xtatish (xost)"),
    ])
    await health_server()
    await restore()
    asyncio.create_task(prune())
    await BOT.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(BOT, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
