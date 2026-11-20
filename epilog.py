# -*- coding: utf-8 -*-
"""Final: jamoani baholash va batafsil hikoya yozish."""
import random
from html import escape as _esc


def escape(s):
    return _esc(str(s), quote=False)

import data as D

# ehtiyoj qoplanganda (ism, manba) bilan hikoya qatori
COVERED = {
    "med": [
        "{who} bunkerning shifokoriga aylandi. Kichik jarohatlar, shamollashlar va bir marta tish og'rig'i — hammasi uning qo'lida hal bo'ldi.",
        "{who} tibbiy masalalarni o'z zimmasiga oldi. Birinchi qishda tarqalgan yo'talni u bir haftada to'xtatdi.",
    ],
    "food": [
        "{who} oziq-ovqat masalasini hal qildi. Bir necha oy o'tib bunkerda o'z hosilimiz paydo bo'ldi — oz bo'lsa ham, yangi.",
        "Ovqat uchun {who} javob berdi. Zaxira kamaya boshlaganda ham hech kim och qolmadi.",
    ],
    "tech": [
        "{who} bunkerning ustasiga aylandi: quvurlar, ventilyatsiya, eshik — hammasi uning nazoratida ishladi.",
        "Texnik muammolar paydo bo'lganda hamma {who}ga qaradi. U hech qachon 'bo'lmaydi' demadi.",
    ],
    "energy": [
        "Energiya va issiqlik uchun {who} javob berdi. Tashqarida bo'ron bo'lsa ham, bunkerda chiroq yonib turdi.",
        "{who} tufayli bunkerda elektr uzilmadi, qish kechalari esa issiq o'tdi.",
    ],
    "defense": [
        "{who} himoyani tashkil qildi. Bir kecha bunker eshigini kimdir buzmoqchi bo'ldi — {who} tufayli ular ortga qaytdi.",
        "Xavfsizlik {who}ning zimmasida edi. Navbatchilik jadvali tuzildi va hech kim kutilmagan mehmondan qo'rqmadi.",
    ],
    "psy": [
        "{who} jamoaning ruhiy tayanchiga aylandi. Eng og'ir kunlarda ham kimdir kulgan bo'lsa, bu uning xizmati.",
        "{who} tufayli bunkerda janjallar tez yarashtirildi, kechqurunlar esa gurung bilan o'tdi.",
    ],
    "know": [
        "{who}ning bilimi bebaho bo'ldi: suvni qanday tozalash, qaysi o'simlik zaharli — hammasini u bilardi.",
        "{who} jamoaning 'ensiklopediyasi' bo'ldi. Har bir muammoga ilmiy yechim topdi.",
    ],
    "comm": [
        "{who} aloqa o'rnatdi: bir kuni radiodan boshqa bunkerning ovozi eshitildi. Dunyoda yolg'iz emasligimizni bildik.",
        "{who} tashqi dunyo bilan aloqani yo'lga qo'ydi va qayerda xavfsiz ekanini birinchi bo'lib bildi.",
    ],
}

MISSING = {
    "med": "Jamoada tibbiyotni biladigan hech kim yo'q edi. Oddiy shamollash ham haftalab davom etdi, kichik jarohat esa katta muammoga aylandi.",
    "food": "Oziq-ovqat yetishtira oladigan odam bo'lmadi. Zaxira tugay boshlaganda kunlik ratsion ikki qoshiq guruchga tushdi.",
    "tech": "Hech kim texnikani tuzatishni bilmasdi. Biror narsa buzilsa, u shunchaki buzilib qoldi.",
    "energy": "Energiya bilan ishlay oladigan odam yo'q edi. Ko'p kechalar qorong'i va sovuq o'tdi.",
    "defense": "Himoyani tashkil qiladigan odam bo'lmadi. Har bir shitirlashdan hamma cho'chib uyg'ondi.",
    "psy": "Jamoaning kayfiyatini ko'taradigan odam bo'lmadi. Bir necha oydan keyin hamma bir-biridan charchadi.",
    "know": "Kerakli bilim yetishmadi. Ko'p qarorlar 'menimcha shunday' degan taxmin bilan qabul qilindi.",
    "comm": "Tashqi dunyo bilan aloqa o'rnatilmadi. Bunkerdagilar tashqarida nima bo'layotganini umuman bilmadi.",
}

PROBLEM_FIXED = "«{p}» muammosini {who} birinchi haftadayoq hal qildi."
PROBLEM_FIXED_CARD = "«{p}» muammosi o'yin davomida tuzatilgan edi — bu katta yengillik bo'ldi."
PROBLEM_LEFT = "«{p}» muammosi hech qachon to'liq hal bo'lmadi va bunkerdagi hayotni ancha og'irlashtirdi."

FUNNY = [
    "{name} bo'sh vaqtlarida «{hobbi}» bilan shug'ullanib, kimnidir xursand qildi, kimnidir esa asabiylashtirdi.",
    "Bunkerning eng kulgili lahzasi: {name} o'zining «{yuk}»ini birinchi marta ochganda hamma bir daqiqa jim qoldi.",
    "{name}ning «{xarakter}» xarakteri birinchi oydayoq hammaga ma'lum bo'ldi.",
    "{name} har kuni ertalab «{yuk}»iga qarab: 'Hali kerak bo'ladi', — deb qo'ydi.",
    "Kechki gurunglarda {name} doim bir xil hikoyani aytdi: «{fakt}». 40-marta ham hamma kulgandek qildi.",
]

TIER = [
    (80, "🟢", "To'liq g'alaba",
     "{months} oydan keyin bunker eshigi ochildi. Hamma tirik, sog'-salomat. Quyosh nuri ko'zni qamashtirdi, lekin bu dunyodagi eng chiroyli manzara edi. Insoniyat yangi sahifani boshlaydi — va uni aynan siz yozasiz."),
    (60, "🟡", "Qiyinchilik bilan, lekin omon qolishdi",
     "{months} oy davom etgan qiyinchiliklardan keyin bunker eshigi ochildi. Hamma ham yaxshi holatda emas, lekin tirik. Ular ancha ozib, ancha jim bo'lib qolgan, ammo kelajakka umid bor."),
    (40, "🟠", "Omon qolish yarim-yarim",
     "Bunkerdagi hayot oson kechmadi. {months} oydan keyin eshik ochilganda, ichkaridagilarning faqat bir qismi tashqariga o'z oyog'i bilan chiqdi. Qolganlari qiyinchiliklarga dosh berolmadi."),
    (0, "🔴", "Bunker ham qutqarmadi",
     "Afsus, bu jamoa omon qololmadi. Zaxira tugadi, muammolar yechilmadi va bir kuni bunkerdan tovush chiqmay qoldi. Tashqaridagilar bilan joy almashsa yaxshiroq bo'larmidi?.."),
]


def _src_name(p, kind):
    c = p["cards"][kind]
    if kind == "kasb":
        return c["name"].split(" (")[0].lower()
    return c["t"].split(" (")[0]


def _who(p, kind):
    name = f"<b>{escape(p['name'])}</b>"
    c = p["cards"][kind]
    if kind == "kasb":
        return f"{escape(c['name'].split(' (')[0].lower())} {name}"
    if kind == "hobbi":
        return f"{escape(c['t'].split(' (')[0].lower())} ishqibozi {name}"
    if kind == "yuk":
        return f"«{escape(c['t'])}» olib kelgan {name}"
    return name


def evaluate(g):
    """Ehtimollik foizi va tafsilotlarni hisoblaydi."""
    team = g.alive()
    cat = g.cat
    needs = list(cat["needs"])
    contrib = {n: [] for n in D.NEED_NAMES}   # need -> [(weight, player, kind)]

    for p in team:
        for kind, w in (("kasb", 2), ("hobbi", 1), ("yuk", 1), ("fakt", 1)):
            c = p["cards"][kind]
            for tag in c.get("tags", []):
                ww = w
                if kind == "kasb" and c.get("exp", 0) == 0:
                    ww = 1
                contrib[tag].append((ww, p, kind))
    equip_tags = {e[1] for e in g.bunker["equip"]}

    score = 50
    details = {"covered": [], "partial": [], "missing": [], "notes": []}
    for need in needs:
        w = sum(x[0] for x in contrib[need]) + (1 if need in equip_tags else 0)
        if w >= 2:
            score += 11
            details["covered"].append(need)
        elif w == 1:
            score += 4
            details["partial"].append(need)
        else:
            score -= 12
            details["missing"].append(need)

    # oziq-ovqat zaxirasi
    supply, wait = g.bunker["supply"], cat["wait"]
    food_ok = sum(x[0] for x in contrib["food"]) + (1 if "food" in equip_tags else 0) >= 2
    if supply >= wait:
        score += 8
    elif food_ok:
        score -= 2
    else:
        score -= 14

    # bunker muammosi
    prob_text, fix_tag, prob_key = g.bunker["problem"]
    fixer = None
    if not g.bunker["fixed"] and contrib[fix_tag]:
        fixer = max(contrib[fix_tag], key=lambda x: x[0])[1]
    if not g.bunker["fixed"] and not fixer:
        score -= 8

    # sog'liq va yosh
    for p in team:
        hs = p["cards"]["sogliq"]["s"]
        if hs < 0:
            score += hs * 3
        age = p["cards"]["bio"]["age"]
        if age >= 65:
            score -= 4

    # ziddiyatlar va xarakterlar
    psy_ok = len(contrib["psy"]) > 0
    conflicts = []
    for p in team:
        fk = p["cards"]["fobiya"].get("k")
        nm = escape(p["name"])
        if fk == "claustro":
            score -= 2 if psy_ok else 7
            conflicts.append(f"{nm}ning klaustrofobiyasi bunkerda kuchaydi — birinchi oylarda u tunlari uxlolmay, eshik oldida o'tirdi.")
        if fk == "dark" and prob_key == "light":
            score -= 4
            conflicts.append(f"Yorug'lik kuniga 6 soat ishlagani {nm} uchun haqiqiy azob bo'ldi — u qorong'ilikdan qo'rqardi.")
        if fk == "rats" and prob_key == "rats":
            score -= 3
            conflicts.append(f"Bunkerdagi kalamushlar va {nm}ning ulardan qo'rqishi... bu haqda gapirmaslik ma'qul.")
        if fk == "blood" and "med" in p["cards"]["kasb"]["tags"]:
            conflicts.append(f"Qondan qo'rqadigan shifokor — {nm} har operatsiyadan oldin ko'zini yumib oldi.")
    traits = [p["cards"]["xarakter"].get("k") for p in team]
    if traits.count("angry") >= 2:
        score -= 6
        conflicts.append("Ikki jahldor odam bitta bunkerda — kunora janjal bo'lib turdi, bir marta hatto oxirgi konserva uchun.")
    if "liar" in traits:
        score -= 3
        liar = [p for p in team if p["cards"]["xarakter"].get("k") == "liar"][0]
        conflicts.append(f"{escape(liar['name'])} zaxiradan yashirincha shokolad olib, keyin kalamushlarga to'nkadi.")
    if "greedy" in traits:
        score -= 3
        gr = [p for p in team if p["cards"]["xarakter"].get("k") == "greedy"][0]
        conflicts.append(f"{escape(gr['name'])} o'z karavoti ostida shaxsiy 'ombor' yig'ib qo'ygani ma'lum bo'ldi.")
    if "lazy" in traits:
        score -= 2
    if "snore" in traits:
        sn = [p for p in team if p["cards"]["xarakter"].get("k") == "snore"][0]
        conflicts.append(f"{escape(sn['name'])}ning xurragi ventilyatsiyadan ham baland edi. Quloqchinlar eng qimmat valyutaga aylandi.")
    if "leader" in traits:
        score += 4
    if "funny" in traits:
        score += 3
    if "worker" in traits:
        score += 3
    if "calm" in traits:
        score += 2

    # kelajak avlod
    m = any(p["cards"]["bio"]["sex"] == "m" and 18 <= p["cards"]["bio"]["age"] <= 45 for p in team)
    f = any(p["cards"]["bio"]["sex"] == "f" and 18 <= p["cards"]["bio"]["age"] <= 45 for p in team)
    future = m and f
    score += 6 if future else -6

    score = max(3, min(97, score))
    return {
        "score": score, "details": details, "contrib": contrib, "fixer": fixer,
        "conflicts": conflicts, "future": future, "food_ok": food_ok,
    }


def _best(contrib, need, used):
    lst = sorted(contrib[need], key=lambda x: -x[0])
    for w, p, kind in lst:
        if p["uid"] not in used:
            return p, kind
    return (lst[0][1], lst[0][2]) if lst else (None, None)


def story(g, ev):
    """Batafsil epilog matni (HTML)."""
    team = g.alive()
    cat, b = g.cat, g.bunker
    score = ev["score"]
    months = cat["wait"] + random.randint(0, 6)
    lines = []
    lines.append(f"🚪 <b>BUNKER ESHIGI YOPILDI</b>\n")
    lines.append("<b>Ichkarida:</b>")
    for p in team:
        lines.append(f"• {escape(p['name'])} — {escape(p['cards']['kasb']['name'])}, {p['cards']['bio']['age']} yosh")
    lines.append("")
    lines.append(f"<b>Omon qolish ehtimoli: {score}%</b>")
    bar = "▰" * round(score / 10) + "▱" * (10 - round(score / 10))
    lines.append(bar)
    lines.append("")

    # Birinchi kunlar
    lines.append("<b>Birinchi kunlar</b>")
    lines.append(
        f"Tashqarida {cat['name'].lower()} davom etardi. {escape(b['place'])} ichida "
        f"{len(team)} kishi bir-biriga qarab o'tirdi: endi ular kamida {cat['wait']} oy birga yashashi kerak edi. "
        f"Zaxira — {b['supply']} oyga."
    )
    # muammo
    prob = b["problem"][0]
    if b["fixed"]:
        lines.append(PROBLEM_FIXED_CARD.format(p=prob))
    elif ev["fixer"]:
        lines.append(PROBLEM_FIXED.format(p=prob, who=f"<b>{escape(ev['fixer']['name'])}</b>"))
    else:
        lines.append(PROBLEM_LEFT.format(p=prob))
    lines.append("")

    # ehtiyojlar
    lines.append("<b>Bunkerdagi hayot</b>")
    used = set()
    for need in cat["needs"]:
        if need in ev["details"]["covered"] or need in ev["details"]["partial"]:
            p, kind = _best(ev["contrib"], need, used)
            if p:
                used.add(p["uid"])
                who = _who(p, kind)
                txt = random.choice(COVERED[need]).format(who=who)
                txt = txt[0].upper() + txt[1:] if not txt.startswith("<") else txt
                if need in ev["details"]["partial"]:
                    txt += " Lekin bitta odam hamma ishga ulgurmasdi."
                lines.append(txt)
            else:  # faqat bunker jihozi qopladi
                eq = [e[0] for e in b["equip"] if e[1] == need][0]
                lines.append(f"Bunkerdagi «{eq}» {D.NEED_NAMES[need]} masalasida qisman yordam berdi, lekin uni ishlata oladigan mutaxassis yo'q edi.")
        else:
            lines.append(MISSING[need])
    # zaxira
    if b["supply"] >= cat["wait"]:
        lines.append(f"Oziq-ovqat zaxirasi ({b['supply']} oy) yetarli bo'ldi — bu eng katta omad edi.")
    elif ev["food_ok"]:
        lines.append(f"Zaxira {b['supply']} oyda tugadi, lekin o'z hosili tufayli jamoa ochlikdan saqlandi.")
    else:
        lines.append(f"Zaxira {b['supply']} oyda tugadi. Qolgan oylar ochlik bilan o'tdi.")
    lines.append("")

    # ziddiyatlar va kulgili lahzalar
    extra = list(ev["conflicts"])
    random.shuffle(extra)
    funny_src = random.sample(team, min(2, len(team)))
    fun = []
    for p in funny_src:
        c = p["cards"]
        fun.append(random.choice(FUNNY).format(
            name=f"<b>{escape(p['name'])}</b>", hobbi=escape(c["hobbi"]["t"]),
            yuk=escape(c["yuk"]["t"]), xarakter=escape(c["xarakter"]["t"].lower()),
            fakt=escape(c["fakt"]["t"].lower())))
    if extra or fun:
        lines.append("<b>Ichkaridagi voqealar</b>")
        for t in extra[:3]:
            lines.append(t)
        for t in fun:
            lines.append(t)
        lines.append("")

    # kelajak
    if not ev["future"]:
        lines.append("<i>Yana bir muammo: jamoada yangi avlodni davom ettira oladigan juftlik yo'q edi. Hatto omon qolishsa ham, insoniyat kelajagi savol ostida.</i>\n")

    # yakun
    for thr, icon, title, text in TIER:
        if score >= thr:
            lines.append(f"{icon} <b>{title}</b>")
            lines.append(text.format(months=months))
            break
    lines.append("")

    # kuchli/zaif
    strong = [D.NEED_NAMES[n] for n in ev["details"]["covered"]]
    weak = [D.NEED_NAMES[n] for n in ev["details"]["missing"]]
    if strong:
        lines.append(f"💪 Kuchli tomon: {', '.join(strong)}")
    if weak:
        lines.append(f"⚠️ Zaif tomon: {', '.join(weak)}")
    return "\n".join(lines)


def outside_story(g, score):
    dead = g.dead()
    if not dead:
        return ""
    lines = ["🌫 <b>TASHQARIDA QOLGANLAR</b>\n"]
    bad = random.sample(D.OUTSIDE_FATES_BAD, len(D.OUTSIDE_FATES_BAD))
    goodl = random.sample(D.OUTSIDE_FATES_GOOD, len(D.OUTSIDE_FATES_GOOD))
    for i, p in enumerate(dead):
        good = random.random() < (0.12 if score >= 50 else 0.3) and goodl
        if good:
            tpl = goodl.pop()
        else:
            if not bad:
                bad = random.sample(D.OUTSIDE_FATES_BAD, len(D.OUTSIDE_FATES_BAD))
            tpl = bad.pop()
        lines.append("• " + tpl.format(name=f"<b>{escape(p['name'])}</b>"))
    return "\n".join(lines)


def mvp(g):
    team = g.alive()
    if not team:
        return None
    return min(team, key=lambda p: p["votes_got"])
