# -*- coding: utf-8 -*-
"""Barcha xabar matnlari va tugmalar."""
import time
from urllib.parse import quote

from aiogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M

import data as D

LINE = "━━━━━━━━━━━━━━━"

PHASES = {
    "intro": "📖 Vaziyat bilan tanishish",
    "turn": "🃏 Karta ochish",
    "reveal": "🃏 Karta ochish",
    "discuss": "💬 Muhokama",
    "vote": "🗳 Ovoz berish",
    "defense": "🛡 Himoya so'zi",
    "revote": "🗳 Qayta ovoz",
    "lastword": "🎤 Oxirgi so'z",
}


def kb(rows):
    return M(inline_keyboard=[r for r in rows if r])


def fmt_time(sec):
    sec = max(0, int(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def time_left(g):
    if g.paused_left is not None:
        return "⏸ pauza"
    if not g.deadline:
        return ""
    return "⏱ " + fmt_time(g.deadline - time.time())


def settings_line(g):
    s = g.settings
    parts = [f"Muhokama {s['discuss']} s", "Ovoz " + ("yashirin" if s["secret"] else "ochiq")]
    parts.append("Maxsus karta ✓" if s["specials"] else "Maxsus karta ✗")
    if s["fast"]:
        parts.append("⚡ Tezkor")
    return " · ".join(parts)


def join_link(bot_username, g):
    return f"https://t.me/{bot_username}?start=j{g.id}"


# ======================================================== LOBBY

def lobby(g, bot_username):
    n = len(g.order)
    lines = ["🏚 <b>BUNKER</b> · yangi o'yin", "",
             "Dunyo halokat yoqasida. Bunkerga hamma sig'maydi — kim kirishini ovoz bilan hal qilasiz.", ""]
    lines.append(f"👥 <b>O'yinchilar ({n}/14)</b>")
    if not g.order:
        lines.append("<i>Hali hech kim yo'q</i>")
    for i, u in enumerate(g.order, 1):
        p = g.players[u]
        lines.append(f"{i}. {p['name']}" + (" 👑" if u == g.host else ""))
    lines.append("")
    if n < 4:
        lines.append(f"Boshlash uchun yana <b>{4 - n}</b> kishi kerak.")
        lines.append("<i>Odam yetmasa, xost «🤖 Bot qo'shish» bilan sun'iy o'yinchilar qo'shishi mumkin.</i>")
    else:
        seats = 2 if n <= 10 else 3
        lines.append(f"✅ Boshlash mumkin. Bunkerda <b>{seats} ta joy</b> bo'ladi.")
    lines.append(f"<i>⚙️ {settings_line(g)}</i>")
    if g.mode == "room":
        link = join_link(bot_username, g)
        lines.append("")
        lines.append(f"🔗 Taklif havolasi:\n{link}")
    rows = [
        [B(text="➕ Qo'shilish", callback_data=f"j:{g.id}"), B(text="➖ Chiqish", callback_data=f"lv:{g.id}")],
        [B(text="🤖 Bot qo'shish", callback_data=f"ab:{g.id}")]
        + ([B(text="🧹 Botlarni olib tashlash", callback_data=f"rb:{g.id}")]
           if any(u.startswith("ai") for u in g.order) else []),
        [B(text="⚙️ Sozlamalar", callback_data=f"set:{g.id}"), B(text="▶️ Boshlash", callback_data=f"st:{g.id}")],
    ]
    if g.mode == "room":
        link = join_link(bot_username, g)
        share = f"https://t.me/share/url?url={quote(link)}&text={quote('Bunker o‘ynaymiz! Qo‘shil 👇')}"
        rows.insert(1, [B(text="📤 Do'stlarni taklif qilish", url=share)])
        rows.append([B(text="✖️ Xonani yopish", callback_data=f"cl:{g.id}")])
    return "\n".join(lines), kb(rows)


def settings(g):
    s = g.settings
    text = ("⚙️ <b>O'yin sozlamalari</b>\n\n"
            "Tugmani bossangiz, qiymat almashadi. Standart qiymatlar bilan ham o'yin yaxshi o'tadi.")
    rows = [
        [B(text=f"💬 Muhokama: {s['discuss']} s", callback_data=f"sg:{g.id}:discuss")],
        [B(text=f"🃏 Kartani tanlash: {s['reveal']} s", callback_data=f"sg:{g.id}:reveal")],
        [B(text=f"🎤 Gapirish navbati: {s.get('speak', 30)} s", callback_data=f"sg:{g.id}:speak")],
        [B(text="🗳 Ovoz: " + ("Yashirin" if s["secret"] else "Ochiq"), callback_data=f"sg:{g.id}:secret")],
        [B(text="✨ Maxsus kartalar: " + ("Yoqilgan" if s["specials"] else "O'chirilgan"), callback_data=f"sg:{g.id}:specials")],
        [B(text="⚡ Tezkor rejim: " + ("Yoqilgan" if s["fast"] else "O'chirilgan"), callback_data=f"sg:{g.id}:fast")],
        [B(text="✅ Tayyor", callback_data=f"sgx:{g.id}")],
    ]
    return text, kb(rows)


# ======================================================== SSENARIY

def scenario(g):
    c, b = g.cat, g.bunker
    eq = ", ".join(e[0] for e in b["equip"])
    lines = [
        f"{c['icon']} <b>FALOKAT: {c['name'].upper()}</b>", "",
        c["desc"], "",
        f"⏳ Tashqariga chiqish: kamida <b>{c['wait']} oydan</b> keyin",
        f"👥 Tirik qolgan aholi: {c['pop']}",
        f"⚠️ Xavflar: {c['threats']}",
        "", LINE, "",
        "🏚 <b>BUNKER</b>",
        f"📍 {b['place']}",
        f"📐 {b['area']} m² · 🛏 <b>{g.seats} ta joy</b>",
        f"🥫 Oziq-ovqat: {b['supply']} oyga",
        f"🛠 Jihozlar: {eq}",
        f"🔧 Muammo: {b['problem'][0]}" + (" <i>(tuzatilgan)</i>" if b["fixed"] else ""),
        "",
        f"<i>{len(g.order)} o'yinchidan faqat {g.seats} kishi bunkerga kiradi. "
        f"Kartalaringiz shaxsiy xabarda. Omad!</i>",
    ]
    return "\n".join(lines)


# ======================================================== O'YIN TAXTASI

def _status_mark(g, p):
    if g.phase == "turn":
        order = g.turn_order or []
        if g.turn_idx is not None and 0 <= g.turn_idx < len(order) and order[g.turn_idx] == p["uid"]:
            return " 👉"
        if p["uid"] in order and order.index(p["uid"]) < (g.turn_idx or 0):
            return " ✓"
        return ""
    if g.phase == "reveal":
        return " ✓" if g.need_more(p) == 0 else " ⌛"
    if g.phase in ("discuss", "intro"):
        return " ✅" if p["ready"] else ""
    if g.phase in ("vote", "revote"):
        return " 🗳" if p["uid"] in g.votes else ""
    return ""


def board(g):
    c, b = g.cat, g.bunker
    rem = g.remaining_kicks()
    lines = [
        f"{c['icon']} <b>{c['name'].upper()}</b>",
        f"⏳ {c['wait']} oy · 🛏 {g.seats} joy · 🥫 {b['supply']} oy zaxira",
        f"🔧 {b['problem'][0]}" + (" ✓ tuzatildi" if b["fixed"] else ""),
        LINE,
    ]
    ph = PHASES.get(g.phase, "")
    rnd = "1-raund (tanishuv)" if g.round == 1 else f"{g.round}-raund"
    if g.phase == "intro":
        rnd = "Boshlanishdan oldin"
    if g.state == "done":
        lines.append("🏁 <b>O'yin tugadi</b> · bunkerga kirganlar:")
    else:
        lines.append(f"<b>{rnd}</b> · {ph} · {time_left(g)}")
    if g.state == "done":
        pass
    elif g.phase == "intro":
        lines.append("<i>Vaziyat va kartalaringiz bilan tanishing</i>")
    elif g.round == 1:
        lines.append("<i>Bu raundda ovoz berilmaydi</i>")
    elif rem > 0:
        this = max(0, g.kicks_round - g.kicks_done)
        lines.append(f"<i>Yana {rem} kishi chiqadi · bu raundda {this}</i>")
    lines.append("")
    for p in g.alive():
        mark = " 👑" if p["uid"] == g.host else ""
        lines.append(f"👤 <b>{p['name']}</b>{mark}{_status_mark(g, p)}")
        opened = [k for k in D.CARD_TYPES if k in p["opened"]]
        for k in opened:
            lines.append(f"     {D.CARD_ICONS[k]} {p['cards'][k]['t']}")
        closed = 8 - len(opened)
        if closed:
            lines.append(f"     <i>🔒 yana {closed} ta yopiq</i>")
    dead = g.dead()
    if dead:
        lines.append(LINE)
        lines.append("🌫 Tashqarida: " + ", ".join(p["name"] for p in dead))
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "…"
    return text


def board_kb(g):
    rows = []
    if g.state == "done":
        return None
    if g.phase in ("discuss", "intro"):
        rows.append([B(text="✅ Tayyorman", callback_data=f"rd:{g.id}")])
    rows.append([B(text="🃏 Mening kartalarim", callback_data=f"my:{g.id}")])
    return kb(rows)


# ======================================================== SHAXSIY KARTALAR

def cards(g, p):
    lines = ["🎭 <b>Sizning xarakteringiz</b>", ""]
    for k in D.CARD_TYPES:
        c = p["cards"][k]
        if k in p["opened"]:
            lines.append(f"{D.CARD_ICONS[k]} {D.CARD_LABELS[k]}: <b>{c['t']}</b> 👁")
        else:
            lines.append(f"{D.CARD_ICONS[k]} {D.CARD_LABELS[k]}: {c['t']} 🔒")
    if p.get("action"):
        name, desc, _ = D.ACTIONS[p["action"]]
        if p["action_used"]:
            lines.append(f"\n✨ Maxsus karta: <s>{name}</s> (ishlatilgan)")
        else:
            lines.append(f"\n✨ Maxsus karta: <b>{name}</b>\n<i>{desc}</i>")
    lines.append("\n<i>👁 — hammaga ochiq · 🔒 — faqat siz ko'rasiz</i>")
    lines.append("")
    lines.append(_prompt(g, p))
    return "\n".join(lines).rstrip()


def _prompt(g, p):
    if not p["alive"]:
        if g.phase == "lastword" and g.lastword == p["uid"]:
            return ("🎤 <b>Oxirgi so'z.</b> Xohlasangiz, bitta kartangizni ochib, nega xato qilishganini "
                    "isbotlang. Gapirib bo'lgach «Tugatdim»ni bosing.")
        return "🌫 Siz tashqaridasiz. O'yinni kuzatishda davom etishingiz mumkin."
    if g.phase == "intro":
        return "📖 Vaziyat bilan tanishing va kartalaringizni ko'rib chiqing. Hozircha hech kimga aytmang!"
    if g.phase == "turn":
        order = g.turn_order or []
        cur = order[g.turn_idx] if g.turn_idx is not None and 0 <= g.turn_idx < len(order) else None
        if cur == p["uid"]:
            where = "guruhdagi" if g.mode == "group" else "pastdagi"
            return f"👉 <b>Sizning navbatingiz!</b> Kartani {where} xabar orqali oching."
        return "🃏 Kartalar navbatma-navbat ochilmoqda. Navbatingizni kuting."
    if g.phase == "discuss":
        return "💬 Muhokama ketmoqda. Nega aynan siz bunkerga kirishingiz kerakligini isbotlang!"
    if g.phase in ("vote", "revote"):
        return "🗳 Ovoz berish vaqti."
    if g.phase == "defense":
        return "🛡 Teng ovoz olganlar o'zini himoya qilmoqda."
    return ""


def cards_kb(g, p):
    rows = []
    if (not p["alive"]) and g.phase == "lastword" and g.lastword == p["uid"]:
        btns = []
        if not p.get("lw_open"):
            btns = [B(text=f"{D.CARD_ICONS[k]} {D.CARD_LABELS[k]}", callback_data=f"lw:{g.id}:{k}")
                    for k in g.closed(p)]
        rows += [btns[i:i + 2] for i in range(0, len(btns), 2)]
        rows.append([B(text="✅ Tugatdim", callback_data=f"lwd:{g.id}")])
    if (p["alive"] and p.get("action") and not p["action_used"]
            and g.phase in ("turn", "discuss", "vote", "defense", "revote")):
        rows.append([B(text=f"✨ Ishlatish: {D.ACTIONS[p['action']][0]}", callback_data=f"ac:{g.id}")])
    if p["uid"] == g.host and g.state == "play":
        paused = g.paused_left is not None
        rows.append([
            B(text="▶️ Davom" if paused else "⏸ Pauza", callback_data=f"h:{g.id}:pause"),
            B(text="+30 s", callback_data=f"h:{g.id}:plus"),
            B(text="⏭ O'tkazish", callback_data=f"h:{g.id}:skip"),
        ])
    return kb(rows)


def action_targets(g, p):
    k = p["action"]
    name, desc, need = D.ACTIONS[k]
    if need is None:
        text = f"✨ <b>{name}</b>\n{desc}\n\nIshlatasizmi?"
        rows = [[B(text="✅ Ha, ishlatish", callback_data=f"at:{g.id}:-"),
                 B(text="✖️ Bekor", callback_data=f"atx:{g.id}")]]
        return text, kb(rows)
    pool = [x for x in g.alive() if need == "any" or x["uid"] != p["uid"]]
    text = f"✨ <b>{name}</b>\n{desc}\n\nKimga qo'llaysiz?"
    btns = [B(text=x["name"] + (" (o'zim)" if x["uid"] == p["uid"] else ""),
              callback_data=f"at:{g.id}:{x['uid']}") for x in pool]
    rows = [btns[i:i + 2] for i in range(0, len(btns), 2)]
    rows.append([B(text="✖️ Bekor", callback_data=f"atx:{g.id}")])
    return text, kb(rows)


# ======================================================== OVOZ

def vote_text(g, final=False):
    from game import tally, candidates
    counts = tally(g)
    cands = candidates(g)
    title = "🗳 <b>Qayta ovoz</b>" if g.phase == "revote" else "🗳 <b>Ovoz berish</b>"
    lines = [f"{title} · {g.round}-raund"]
    if g.kicks_round - g.kicks_done > 1 and g.phase == "vote":
        lines.append(f"<i>Bu raundda yana {g.kicks_round - g.kicks_done} kishi chiqadi — navbatma-navbat.</i>")
    lines.append("Kimni bunkerdan chiqaramiz?" + ("" if final else f"  {time_left(g)}"))
    lines.append("")
    if g.settings["secret"] and not final:
        for p in cands:
            lines.append(f"• {p['name']}" + (" 🛡" if p["uid"] in g.effects["immune"] else ""))
    else:
        srt = sorted(cands, key=lambda p: -counts[p["uid"]])
        top = max(counts.values()) if counts else 0
        for p in srt:
            c = counts[p["uid"]]
            bar = "█" * c if c else "·"
            who = [g.players[v]["name"] for v, t in g.votes.items() if t == p["uid"]]
            extra = f"  <i>({', '.join(who)})</i>" if who else ""
            imm = " 🛡" if p["uid"] in g.effects["immune"] else ""
            name = f"<b>{p['name']}</b>" if (c == top and c > 0) else p["name"]
            lines.append(f"{name}{imm}  {bar} {c}{extra}")
    voted = sum(1 for v in g.alive() if v["uid"] in g.votes)
    lines.append("")
    lines.append(f"Ovoz berdi: {voted}/{len(g.alive())}")
    notes = []
    if g.effects["double"]:
        notes.append("✌️ ikki ovoz: " + ", ".join(g.players[u]["name"] for u in g.effects["double"]))
    if g.effects["veto"]:
        notes.append("🚫 veto: " + ", ".join(g.players[u]["name"] for u in g.effects["veto"]))
    if notes:
        lines.append("<i>" + " · ".join(notes) + "</i>")
    return "\n".join(lines)


def vote_kb(g, voter=None):
    from game import candidates
    btns = []
    for p in candidates(g):
        if voter and p["uid"] == voter:
            continue
        mark = "✓ " if voter and g.votes.get(voter) == p["uid"] else ""
        btns.append(B(text=f"{mark}{p['name']}", callback_data=f"v:{g.id}:{g.vote_seq}:{p['uid']}"))
    rows = [btns[i:i + 2] for i in range(0, len(btns), 2)]
    return kb(rows)


# ======================================================== FINAL

def final_kb(g):
    return kb([
        [B(text="🃏 Barcha kartalar", callback_data=f"fc:{g.id}")],
        [B(text="🔁 Yana o'ynash", callback_data=f"again:{g.id}")],
    ])


def all_cards(g):
    lines = ["🃏 <b>Barcha kartalar</b>", ""]
    for p in g.all_players():
        st = "🏚 bunkerda" if p["alive"] else "🌫 tashqarida"
        lines.append(f"<b>{p['name']}</b> — {st}")
        for k in D.CARD_TYPES:
            lines.append(f"  {D.CARD_ICONS[k]} {p['cards'][k]['t']}")
        if p.get("action"):
            lines.append(f"  ✨ {D.ACTIONS[p['action']][0]}" + (" (ishlatilgan)" if p["action_used"] else ""))
        lines.append("")
    return "\n".join(lines)


# ======================================================== MENYU

def welcome(bot_username):
    text = ("🏚 <b>Bunker</b> — do'stlar bilan o'ynaladigan omon qolish o'yini.\n\n"
            "Dunyoda falokat yuz berdi. Bunkerga hamma sig'maydi. Har kimga yashirin xarakter "
            "beriladi: kasb, yosh, sog'liq, hobbi, fobiya va boshqalar. Kartalarni ochib, bahslashib, "
            "ovoz bilan kim bunkerga kirishini hal qilasiz.\n\n"
            "👥 4–14 o'yinchi · ⏱ 20–40 daqiqa\n\n"
            "<b>Qanday boshlash mumkin:</b>\n"
            "• <b>Guruhda</b> — botni guruhga qo'shing va /bunker yozing.\n"
            "• <b>Guruhsiz</b> — pastdagi «Xona yaratish»ni bosing va havolani do'stlaringizga yuboring.")
    return text, kb([
        [B(text="🏠 Xona yaratish (guruhsiz)", callback_data="m:new")],
        [B(text="➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=bunker")],
        [B(text="📖 Qoidalar", callback_data="m:rules"), B(text="👤 Profil", callback_data="m:profile")],
    ])


# ======================================================== NAVBAT

def _progress(g):
    n = len(g.turn_order or [])
    return f"{(g.turn_idx or 0) + 1}/{n}" if n else ""


def turn_choose(g, p, mention):
    from game import allowed_types
    allowed = allowed_types(g, p)
    lines = [f"🎯 <b>Navbat:</b> {mention}  <i>({_progress(g)})</i>", ""]
    if g.round == 1:
        lines.append("💼 <b>Kasb</b> kartangizni oching va o'zingizni qisqacha tanishtiring.")
    elif g.turn_idx == 0 or not g.round_type:
        lines.append("Siz raundni boshlaysiz: <b>qaysi turdagi kartani ochasiz?</b>\n"
                     "Qolganlar ham aynan shu turdagi kartani ochadi.")
    elif g.round_type in allowed:
        k = g.round_type
        lines.append(f"Bu raund kartasi: {D.CARD_ICONS[k]} <b>{D.CARD_LABELS[k]}</b>. Oching!")
    else:
        k = g.round_type
        lines.append(f"Sizning {D.CARD_LABELS[k].lower()} kartangiz allaqachon ochiq — istalgan boshqa kartani tanlang.")
    lines.append("")
    lines.append(f"⏱ {g.phase_time('choose')} s · vaqt tugasa, karta avtomatik ochiladi")
    return "\n".join(lines)


def turn_choose_kb(g, p):
    from game import allowed_types
    allowed = allowed_types(g, p)
    if len(allowed) == 1:
        k = allowed[0]
        btns = [[B(text=f"🃏 Ochish: {D.CARD_ICONS[k]} {D.CARD_LABELS[k]}",
                   callback_data=f"tc:{g.id}:{g.turn_seq}:{k}")]]
    else:
        bb = [B(text=f"{D.CARD_ICONS[k]} {D.CARD_LABELS[k]}", callback_data=f"tc:{g.id}:{g.turn_seq}:{k}")
              for k in allowed]
        btns = [bb[i:i + 2] for i in range(0, len(bb), 2)]
    btns.append([B(text="👀 Kartalarimni ko'rish", callback_data=f"my:{g.id}")])
    return kb(btns)


def turn_card(g, p, kind, auto=False, talking=True):
    c = p["cards"][kind]
    head = f"🃏 <b>{p['name']}</b> kartasini ochdi" + (" <i>(vaqt tugadi, avtomatik)</i>" if auto else "")
    lines = [head, "", LINE,
             f"{D.CARD_ICONS[kind]}  <b>{D.CARD_LABELS[kind].upper()}</b>",
             f"<b>{c['t']}</b>",
             LINE]
    prev = [k for k in D.CARD_TYPES if k in p["opened"] and k != kind]
    if prev:
        lines.append("<i>Avval ochilgan: " + " · ".join(f"{D.CARD_ICONS[k]} {p['cards'][k]['t']}" for k in prev) + "</i>")
    if talking:
        lines.append("")
        lines.append(f"🎤 <b>{p['name']}</b> gapirmoqda · ⏱ {g.phase_time('talk')} s")
    return "\n".join(lines)


def turn_talk_kb(g):
    return kb([[B(text="⏭ Tugatdim", callback_data=f"td:{g.id}:{g.turn_seq}")]])
