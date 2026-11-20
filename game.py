# -*- coding: utf-8 -*-
"""O'yin modeli va qoidalar (Telegramdan mustaqil)."""
import math
import random
import secrets
import time

import data as D

MIN_PLAYERS = 4
MAX_PLAYERS = 14
MAX_VOTE_ROUNDS = 6

DEFAULT_SETTINGS = {
    "discuss": 120,   # muhokama, soniya
    "reveal": 30,     # navbatda karta tanlash, soniya
    "speak": 30,      # karta ochilgandan keyin gapirish, soniya
    "secret": False,  # yashirin ovoz
    "specials": True, # maxsus kartalar
    "fast": False,    # tezkor rejim
}

VOTE_TIME = 35
DEFENSE_TIME = 25
LASTWORD_TIME = 25


def seats_for(n: int) -> int:
    return 2 if n <= 10 else 3


def new_id() -> str:
    return secrets.token_hex(3)


def new_player(uid, name):
    return {
        "uid": str(uid), "name": name, "cards": {}, "opened": [], "alive": True,
        "action": None, "action_used": False, "ready": False, "votes_got": 0,
        "out_round": None,
    }


class Game:
    FIELDS = [
        "id", "mode", "chat_id", "host", "settings", "state", "phase", "deadline",
        "paused_left", "round", "players", "order", "cat", "bunker", "seats",
        "vote_rounds", "kicks_round", "kicks_done", "tie", "votes", "vote_seq",
        "lastword", "effects", "open2_next", "open2", "msgs", "history", "created",
        "result", "round_reveals", "phase_started", "joy_used",
        "turn_order", "turn_idx", "round_type", "turn_state", "turn_seq", "cycle",
        "last_turn_kind", "turn_log", "choose_fallback",
    ]

    def __init__(self, gid=None, mode="group", chat_id=None, host=None):
        self.id = gid or new_id()
        self.mode = mode              # "group" | "room"
        self.chat_id = chat_id        # guruh id (room rejimida None)
        self.host = str(host) if host else None
        self.settings = dict(DEFAULT_SETTINGS)
        self.state = "lobby"          # lobby | play | done
        self.phase = None
        self.deadline = None
        self.paused_left = None
        self.round = 0
        self.players = {}
        self.order = []
        self.cat = None
        self.bunker = None
        self.seats = 0
        self.vote_rounds = 0
        self.kicks_round = 0
        self.kicks_done = 0
        self.tie = None
        self.votes = {}
        self.vote_seq = 0
        self.lastword = None
        self.effects = {"immune": [], "double": [], "veto": []}
        self.open2_next = False
        self.open2 = False
        # xabarlar: [[chat_id, message_id], ...]
        self.msgs = {"lobby": [], "board": [], "vote": [], "cards": {}, "turn": [], "choose": None}
        self.history = []
        self.created = time.time()
        self.result = None
        self.round_reveals = {}
        self.phase_started = None
        self.joy_used = False
        self.turn_order = []
        self.turn_idx = -1
        self.round_type = None
        self.turn_state = None
        self.turn_seq = 0
        self.cycle = 0
        self.last_turn_kind = None
        self.turn_log = []
        self.choose_fallback = False

    # ---------------------------------------------------- serializatsiya
    def to_dict(self):
        return {f: getattr(self, f) for f in self.FIELDS}

    @classmethod
    def from_dict(cls, d):
        g = cls()
        for f in cls.FIELDS:
            if f in d:
                setattr(g, f, d[f])
        return g

    # ---------------------------------------------------- yordamchilar
    def p(self, uid):
        return self.players.get(str(uid))

    def alive(self):
        return [self.players[u] for u in self.order if self.players[u]["alive"]]

    def dead(self):
        return [self.players[u] for u in self.order if not self.players[u]["alive"]]

    def all_players(self):
        return [self.players[u] for u in self.order]

    def add_player(self, uid, name):
        uid = str(uid)
        if uid in self.players or len(self.players) >= MAX_PLAYERS:
            return False
        self.players[uid] = new_player(uid, name)
        self.order.append(uid)
        if not self.host:
            self.host = uid
        return True

    def remove_player(self, uid):
        uid = str(uid)
        if uid not in self.players:
            return False
        del self.players[uid]
        self.order.remove(uid)
        if self.host == uid:
            self.host = self.order[0] if self.order else None
        return True

    def remaining_kicks(self):
        return len(self.alive()) - self.seats

    def closed(self, p):
        return [t for t in D.CARD_TYPES if t not in p["opened"]]

    def reveals_needed(self):
        """Shu raundda har bir o'yinchi nechta karta ochishi kerak."""
        if self.round == 1:
            return 1  # hamma kasbini ochadi
        n = 2 if (self.settings.get("fast") or self.open2) else 1
        return n

    def need_more(self, p):
        done = len(self.round_reveals.get(p["uid"], []))
        return max(0, min(self.reveals_needed(), len(self.closed(p)) + done) - done)

    def phase_time(self, phase):
        s = self.settings
        k = 0.6 if s.get("fast") else 1.0
        t = {
            "choose": s["reveal"],
            "talk": s.get("speak", 30),
            "intro": 40,
            "discuss": s["discuss"],
            "vote": VOTE_TIME,
            "defense": DEFENSE_TIME,
            "revote": VOTE_TIME,
            "lastword": LASTWORD_TIME,
        }.get(phase, 30)
        return int(t * k)


# ======================================================== KARTALAR TARQATISH

def _bio(age, sex):
    s = 0
    if 20 <= age <= 45:
        s = 1
    elif 60 <= age <= 69:
        s = -1
    elif age >= 70:
        s = -2
    return {"t": f"{'Erkak' if sex == 'm' else 'Ayol'}, {age} yosh", "age": age,
            "sex": sex, "tags": [], "s": s}


def _kasb(entry, age):
    name, tags, score = entry
    exp = random.randint(0, max(0, min(25, age - 18)))
    if exp == 0:
        t = f"{name} · tajribasiz"
        s = score - 1 if score > 0 else score
    else:
        t = f"{name} · {exp} yil tajriba"
        s = score + (1 if exp >= 10 and score > 0 else 0)
    return {"t": t, "name": name, "exp": exp, "tags": list(tags), "s": s}


def _pool(lst):
    pool = list(lst)
    random.shuffle(pool)
    return pool


def deal(g: Game):
    n = len(g.order)
    g.cat = dict(random.choice(D.CATASTROPHES))
    wait = g.cat["wait"]
    eq = random.sample(D.BUNKER_EQUIP, 3)
    prob = random.choice(D.BUNKER_PROBLEMS)
    g.bunker = {
        "place": random.choice(D.BUNKER_PLACES),
        "area": random.choice(range(60, 310, 10)),
        "supply": max(3, int(round(wait * random.uniform(0.3, 1.15)))),
        "equip": [[e[0], e[1]] for e in eq],
        "problem": [prob[0], prob[1], prob[2]],
        "fixed": False,
    }
    g.seats = seats_for(n)

    profs = _pool(D.PROFESSIONS)
    pools = {
        "sogliq": _pool(D.HEALTH), "hobbi": _pool(D.HOBBIES), "fobiya": _pool(D.PHOBIAS),
        "xarakter": _pool(D.TRAITS), "yuk": _pool(D.LUGGAGE), "fakt": _pool(D.FACTS),
    }

    def take(kind):
        pool = pools[kind]
        if not pool:
            pools[kind] = pool = _pool({"sogliq": D.HEALTH, "hobbi": D.HOBBIES,
                                         "fobiya": D.PHOBIAS, "xarakter": D.TRAITS,
                                         "yuk": D.LUGGAGE, "fakt": D.FACTS}[kind])
        e = pool.pop()
        if kind == "sogliq":
            return {"t": e[0], "tags": [], "s": e[1]}
        if kind in ("fobiya", "xarakter"):
            return {"t": e[0], "k": e[1], "tags": [], "s": e[2]}
        return {"t": e[0], "tags": list(e[1]), "s": e[2]}

    for uid in g.order:
        p = g.players[uid]
        age = int(random.triangular(18, 80, 29))
        sex = random.choice("mf")
        cards = {
            "kasb": _kasb(profs.pop(), age),
            "bio": _bio(age, sex),
        }
        for kind in ("sogliq", "hobbi", "fobiya", "xarakter", "yuk", "fakt"):
            cards[kind] = take(kind)
        p["cards"] = cards
        p["opened"] = []
        p["alive"] = True
        p["action_used"] = False
        p["votes_got"] = 0
        p["out_round"] = None

    _balance(g)

    if g.settings.get("specials"):
        keys = list(D.ACTION_WEIGHTS)
        for uid in g.order:
            while True:
                k = random.choices(keys, weights=[D.ACTION_WEIGHTS[x] for x in keys])[0]
                if k == "joy" and g.joy_used:
                    continue
                if k == "joy":
                    g.joy_used = True
                break
            g.players[uid]["action"] = k
    else:
        for uid in g.order:
            g.players[uid]["action"] = None

    g.vote_rounds = min(n - g.seats, MAX_VOTE_ROUNDS)


def total_score(p):
    return sum(c.get("s", 0) for c in p["cards"].values())


def _balance(g, iters=300):
    """Eng 'boy' va eng 'kambag'al' o'yinchilar o'rtasida kartalarni almashtirib,
    umumiy ballarni yaqinlashtiradi."""
    ps = [g.players[u] for u in g.order]
    swappable = ["sogliq", "hobbi", "fobiya", "xarakter", "yuk", "fakt", "kasb"]
    for _ in range(iters):
        ps.sort(key=total_score)
        lo, hi = ps[0], ps[-1]
        spread = total_score(hi) - total_score(lo)
        if spread <= 3:
            break
        kind = random.choice(swappable)
        a, b = lo["cards"][kind], hi["cards"][kind]
        if a.get("s", 0) >= b.get("s", 0):
            continue
        if kind == "kasb":
            # tajribani yoshga moslab qayta hisoblaymiz
            la, lb = lo["cards"]["bio"]["age"], hi["cards"]["bio"]["age"]
            if b["exp"] > la - 18 or a["exp"] > lb - 18:
                continue
        lo["cards"][kind], hi["cards"][kind] = b, a


# ======================================================== RAUNDLAR

def start_round(g: Game):
    """Yangi raundni boshlash: ochishlar va effektlarni tozalash."""
    g.round += 1
    g.round_reveals = {}
    g.effects = {"immune": [], "double": [], "veto": []}
    g.open2 = g.open2_next
    g.open2_next = False
    g.kicks_done = 0
    g.cycle = 0
    for p in g.alive():
        p["ready"] = False
    if g.round == 1:
        g.kicks_round = 0
    else:
        rem = g.remaining_kicks()
        rem_rounds = g.vote_rounds - (g.round - 2)
        g.kicks_round = rem if rem_rounds <= 1 else math.ceil(rem / rem_rounds)


def allowed_types(g: Game, p):
    """Navbatdagi o'yinchi qaysi kartalarni ocha oladi."""
    cl = g.closed(p)
    if not cl:
        return []
    if g.round == 1:
        return ["kasb"] if "kasb" in cl else cl
    if g.turn_idx == 0 or not g.round_type:
        return cl
    return [g.round_type] if g.round_type in cl else cl


def open_card(g: Game, p, kind):
    if kind not in g.closed(p):
        return False
    p["opened"].append(kind)
    g.round_reveals.setdefault(p["uid"], []).append(kind)
    return True


def auto_reveal(g: Game):
    """Vaqtida ochmaganlar uchun tasodifiy karta ochiladi."""
    auto = []
    for p in g.alive():
        while g.need_more(p) > 0 and g.closed(p):
            kind = random.choice(g.closed(p))
            open_card(g, p, kind)
            auto.append((p, kind))
    return auto


def all_revealed(g: Game):
    return all(g.need_more(p) == 0 for p in g.alive())


def all_ready(g: Game):
    return all(p["ready"] for p in g.alive())


def voters(g: Game):
    return [p for p in g.alive()]


def candidates(g: Game):
    if g.tie:
        return [g.players[u] for u in g.tie if g.players[u]["alive"]]
    return g.alive()


def all_voted(g: Game):
    return all(p["uid"] in g.votes for p in voters(g))


def tally(g: Game):
    cands = candidates(g)
    counts = {p["uid"]: 0 for p in cands}
    for voter, target in g.votes.items():
        if voter in g.effects["veto"]:
            continue
        if target not in counts or target in g.effects["immune"]:
            continue
        counts[target] += 2 if voter in g.effects["double"] else 1
    return counts


def leaders(g: Game, counts):
    pool = {u: c for u, c in counts.items() if u not in g.effects["immune"]}
    if not pool:
        pool = counts
    top = max(pool.values())
    return [u for u, c in pool.items() if c == top], top


def kick(g: Game, uid, counts):
    p = g.players[uid]
    p["alive"] = False
    p["out_round"] = g.round
    for u, c in counts.items():
        g.players[u]["votes_got"] += c
    g.history.append({"round": g.round, "uid": uid, "votes": counts.get(uid, 0)})
    g.kicks_done += 1


# ======================================================== MAXSUS KARTALAR

def use_action(g: Game, p, target=None):
    """Maxsus kartani qo'llash. Qaytaradi: (public_text, private_text) yoki xato matni."""
    k = p["action"]
    if not k or p["action_used"]:
        return None, "Maxsus kartangiz yo'q yoki ishlatilgan."
    name = D.ACTIONS[k][0]
    t = g.players.get(target) if target else None
    who = p["name"]
    pub = priv = None

    if k == "immunitet":
        g.effects["immune"].append(p["uid"])
        pub = f"🛡 <b>{who}</b> «Immunitet» kartasini ishlatdi: shu raundda unga berilgan ovozlar hisoblanmaydi."
    elif k == "ikki_ovoz":
        g.effects["double"].append(p["uid"])
        pub = f"✌️ <b>{who}</b> «Ikki ovoz» kartasini ishlatdi: shu raundda uning ovozi 2 ga teng."
    elif k == "veto":
        g.effects["veto"].append(t["uid"])
        pub = f"🚫 <b>{who}</b> «Veto» ishlatdi: <b>{t['name']}</b>ning shu raunddagi ovozi hisoblanmaydi."
    elif k == "josus":
        cl = g.closed(t)
        if not cl:
            return None, "Bu o'yinchining yopiq kartasi qolmagan. Boshqasini tanlang."
        kind = random.choice(cl)
        priv = (f"🕵️ <b>{t['name']}</b>ning yashirin kartasi:\n"
                f"{D.CARD_ICONS[kind]} {D.CARD_LABELS[kind]}: <b>{t['cards'][kind]['t']}</b>")
        pub = f"🕵️ <b>{who}</b> «Josus» kartasini ishlatdi va kimningdir sirini bilib oldi..."
    elif k == "fosh":
        cl = g.closed(t)
        if not cl:
            return None, "Bu o'yinchining yopiq kartasi qolmagan. Boshqasini tanlang."
        kind = random.choice(cl)
        t["opened"].append(kind)
        pub = (f"🔦 <b>{who}</b> «Fosh qilish» ishlatdi! <b>{t['name']}</b>ning kartasi ochildi:\n"
               f"{D.CARD_ICONS[kind]} {D.CARD_LABELS[kind]}: <b>{t['cards'][kind]['t']}</b>")
    elif k == "shifokor":
        old = t["cards"]["sogliq"]["t"]
        t["cards"]["sogliq"] = {"t": "Mutlaqo sog'lom (davolangan)", "tags": [], "s": 2}
        if "sogliq" in t["opened"]:
            pub = (f"💊 <b>{who}</b> «Shifokor» kartasi bilan <b>{t['name']}</b>ni davoladi: "
                   f"«{old}» → <b>Mutlaqo sog'lom</b>.")
        else:
            pub = f"💊 <b>{who}</b> «Shifokor» kartasi bilan <b>{t['name']}</b>ni davoladi. Nimadan — hozircha sir."
    elif k == "yangi_kasb":
        used = {pp["cards"]["kasb"]["name"] for pp in g.all_players()}
        choices = [e for e in D.PROFESSIONS if e[0] not in used]
        old = p["cards"]["kasb"]["t"]
        p["cards"]["kasb"] = _kasb(random.choice(choices), p["cards"]["bio"]["age"])
        pub = (f"🔄 <b>{who}</b> kasbini almashtirdi: «{old}» → "
               f"<b>{p['cards']['kasb']['t']}</b>")
    elif k == "tamirchi":
        if g.bunker["fixed"]:
            return None, "Bunker muammosi allaqachon tuzatilgan."
        g.bunker["fixed"] = True
        pub = f"🔧 <b>{who}</b> «Ta'mirchi» kartasi bilan bunker muammosini tuzatdi: «{g.bunker['problem'][0]}» — endi hal qilingan."
    elif k == "sabotaj":
        g.bunker["supply"] = max(1, g.bunker["supply"] - 3)
        pub = f"💣 <b>{who}</b> «Sabotaj» qildi! Bunker zaxirasi 3 oyga kamaydi: endi <b>{g.bunker['supply']} oy</b>."
    elif k == "topilma":
        g.bunker["supply"] += 4
        pub = f"📦 <b>{who}</b> omborda yashirin zaxira topdi! Endi zaxira <b>{g.bunker['supply']} oy</b>."
    elif k == "hamma_ochsin":
        g.open2_next = True
        pub = f"🃏 <b>{who}</b> «Hamma ochsin» ishlatdi: keyingi raundda hamma 2 tadan karta ochadi."
    elif k == "joy":
        if g.seats + 1 >= len(g.alive()):
            return None, "Hozir qo'shimcha joy qo'shib bo'lmaydi (deyarli hamma sig'adi)."
        g.seats += 1
        pub = f"🚪 <b>{who}</b> bunkerda yashirin xona topdi! Endi bunkerda <b>{g.seats} ta joy</b>."
    p["action_used"] = True
    return pub, priv
