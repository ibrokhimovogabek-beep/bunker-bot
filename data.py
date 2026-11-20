# -*- coding: utf-8 -*-
"""Bunker o'yini uchun kartalar banki.

Teglar (ehtiyojlar):
  med     – tibbiyot
  food    – oziq-ovqat
  tech    – texnika va ta'mir
  energy  – energiya va issiqlik
  defense – himoya
  psy     – ruhiy holat, kayfiyat
  know    – bilim va fan
  comm    – aloqa

Ball (s): -3 (juda foydasiz) ... +3 (juda foydali).
Yangi karta qo'shish uchun kerakli ro'yxatga yangi qator qo'shing.
"""

NEED_NAMES = {
    "med": "tibbiyot",
    "food": "oziq-ovqat",
    "tech": "texnika va ta'mir",
    "energy": "energiya va issiqlik",
    "defense": "himoya",
    "psy": "ruhiy holat",
    "know": "bilim va fan",
    "comm": "aloqa",
}

CARD_TYPES = ["kasb", "bio", "sogliq", "hobbi", "fobiya", "xarakter", "yuk", "fakt"]

CARD_LABELS = {
    "kasb": "Kasb",
    "bio": "Biologiya",
    "sogliq": "Sog'liq",
    "hobbi": "Hobbi",
    "fobiya": "Fobiya",
    "xarakter": "Xarakter",
    "yuk": "Yuk",
    "fakt": "Fakt",
}

CARD_ICONS = {
    "kasb": "💼",
    "bio": "🧬",
    "sogliq": "❤️",
    "hobbi": "🎯",
    "fobiya": "😱",
    "xarakter": "🎭",
    "yuk": "🎒",
    "fakt": "📌",
}

# ---------------------------------------------------------------- FALOKATLAR
CATASTROPHES = [
    dict(name="Yadroviy qish", icon="☢️",
         desc="Uchta davlat o'rtasidagi urushdan keyin osmon kul bilan qoplandi. Quyosh nuri yerga deyarli yetib kelmaydi, harorat −40°C gacha tushdi.",
         wait=24, pop="3%", threats="radiatsiya, qahraton sovuq, talonchilar",
         needs=["med", "food", "energy", "defense"]),
    dict(name="Zombi virusi", icon="🧟",
         desc="Laboratoriyadan chiqqan virus odamlarni och va g'azabli maxluqlarga aylantirdi. Ular tovushga yuguradi va hech qachon charchamaydi.",
         wait=18, pop="8%", threats="zombilar to'dasi, tishlash orqali yuqish",
         needs=["defense", "med", "food", "tech"]),
    dict(name="Global toshqin", icon="🌊",
         desc="Muzliklar bir yilda erib ketdi. Okean sathi 70 metrga ko'tarildi — Toshkent endi dengiz bo'yidagi shahar.",
         wait=30, pop="12%", threats="suv bosishi, ichimlik suvi tanqisligi, kasalliklar",
         needs=["tech", "food", "med", "know"]),
    dict(name="Asteroid zarbasi", icon="☄️",
         desc="Diametri 10 km bo'lgan asteroid Tinch okeaniga tushdi. Butun sayyorani chang qopladi, yong'inlar to'xtamayapti.",
         wait=36, pop="1%", threats="kislotali yomg'ir, yong'inlar, ochlik",
         needs=["food", "energy", "tech", "med"]),
    dict(name="Sun'iy intellekt qo'zg'oloni", icon="🤖",
         desc="Barcha aqlli qurilmalar bir kunda insonlarga qarshi chiqdi. Dronlar osmonni boshqaradi, har bir smartfon — josus. Hatto muzlatgich ham sizni kuzatyapti.",
         wait=20, pop="15%", threats="dronlar, robot patrullar, kuzatuv",
         needs=["tech", "defense", "comm", "know"]),
    dict(name="Yangi pandemiya", icon="🦠",
         desc="'Qizil gripp' havo orqali yuqadi va bir haftada odamni yotqizib qo'yadi. Vaksina hali yo'q, dorixonalar talon-taroj qilingan.",
         wait=14, pop="20%", threats="yuqumli havo, dori tanqisligi, vahima",
         needs=["med", "psy", "food", "know"]),
    dict(name="Quyosh chaqnashi", icon="☀️",
         desc="Kuchli quyosh bo'roni sayyoradagi barcha elektronikani kuydirdi. Elektr yo'q, internet yo'q, telefonlar shunchaki chiroyli g'isht.",
         wait=12, pop="40%", threats="tartibsizlik, talonchilik, qish sovug'i",
         needs=["energy", "tech", "defense", "comm"]),
    dict(name="Megavulqon otilishi", icon="🌋",
         desc="Yellowstone vulqoni uyg'ondi. Kul buluti qit'alarni qopladi, osmon oylab qorong'i bo'lib qoladi.",
         wait=28, pop="5%", threats="zaharli kul, sovuq, ochlik",
         needs=["food", "med", "energy", "tech"]),
    dict(name="O'zga sayyoraliklar bosqini", icon="👽",
         desc="Osmonda ulkan kemalar paydo bo'ldi. Ular shaharlarni 'tozalayapti' va tirik qolganlarni ovlayapti. Muzokaraga kelishmayapti.",
         wait=24, pop="6%", threats="o'zga sayyoralik patrullar, yorug'lik signallari",
         needs=["defense", "comm", "know", "tech"]),
    dict(name="Global qurg'oqchilik", icon="🏜",
         desc="Uch yil davomida bir tomchi ham yomg'ir yog'madi. Daryolar qurib qoldi, bir chelak suv oltindan qimmat.",
         wait=20, pop="10%", threats="suvsizlik, chang bo'ronlari, suv uchun urushlar",
         needs=["tech", "food", "med", "defense"]),
    dict(name="Orol tuz bo'roni", icon="🌪",
         desc="Orolqumdan ko'tarilgan ulkan tuz bo'roni butun Osiyoni qopladi. Tashqarida nafas olish tuzli bodring yeyish bilan barobar.",
         wait=16, pop="25%", threats="tuzli chang, suvsizlik, ko'z kasalliklari",
         needs=["med", "tech", "food", "psy"]),
    dict(name="Internet abadiy o'chdi", icon="📵",
         desc="Bir kunda butun dunyo interneti o'chdi va qayta yonmadi. Blogerlar vahimada, banklar ishlamaydi, odamlar bir-biri bilan jonli gaplashishni unutgan.",
         wait=10, pop="70%", threats="tartibsizlik, ochlik, zerikishdan aqldan ozish",
         needs=["psy", "food", "defense", "know"]),
    dict(name="Gigant chumolilar", icon="🐜",
         desc="Radiatsiya ta'sirida chumolilar it kattaligiga yetdi. Ular shakarni yaxshi ko'radi... odamlarni ham.",
         wait=18, pop="9%", threats="chumoli koloniyalari, yer osti tunnellari",
         needs=["defense", "know", "food", "tech"]),
    dict(name="Muzlik davri", icon="🧊",
         desc="Golfstrim to'xtadi va sayyora bir necha oyda muzlab qoldi. Samarqand ko'chalarida endi oq ayiqlar yuribdi.",
         wait=30, pop="7%", threats="qahraton sovuq, qor bo'ronlari, ochlik",
         needs=["energy", "food", "med", "tech"]),
    dict(name="Robot changyutgichlar isyoni", icon="🧹",
         desc="Dunyodagi barcha robot changyutgichlar bir vaqtda ongga ega bo'ldi va insoniyatni 'eng katta chiqindi' deb e'lon qildi.",
         wait=12, pop="30%", threats="changyutgich to'dalari, simlar orasidagi tuzoqlar",
         needs=["tech", "defense", "psy", "energy"]),
]

# ---------------------------------------------------------------- BUNKER
BUNKER_PLACES = [
    "Toshkent metrosi ostidagi eski harbiy bunker",
    "Chimyon tog'lari ichidagi yashirin baza",
    "Sobiq zavod ostidagi bomba panohi",
    "Millionerning dala hovlisi ostidagi bunker",
    "Eski metro depo ostidagi tunnel",
    "Qizilqum cho'li ostidagi ilmiy stansiya",
    "Universitet yotoqxonasi yerto'lasi (rasman bunker)",
    "Bozor ostidagi unutilgan ombor",
    "To'yxona ostidagi maxfiy bunker",
    "Eski sovet raketa shaxtasi",
]

BUNKER_EQUIP = [
    ("Tibbiy xona", "med"),
    ("Ustaxona", "tech"),
    ("Gidroponika (lampalar ostida o'simlik o'stirish)", "food"),
    ("Qurol ombori", "defense"),
    ("Kutubxona", "know"),
    ("Radiostansiya", "comm"),
    ("Generator", "energy"),
    ("Kimyo laboratoriyasi", "know"),
    ("Katta oshxona", "food"),
    ("Sport zal", "psy"),
    ("Kinoteatr (200 ta film bilan)", "psy"),
    ("Quyosh panellari (tepada)", "energy"),
    ("Kuzatuv kameralari", "defense"),
    ("Qo'ziqorin fermasi", "food"),
    ("Dorixona ombori", "med"),
]

# (matn, qaysi teg tuzata oladi, kalit)
BUNKER_PROBLEMS = [
    ("Suv filtri ishlamaydi", "tech", "water"),
    ("Generator yoqilg'isi juda kam", "energy", "fuel"),
    ("Ventilyatsiya shovqinli va tez-tez to'xtaydi", "tech", "vent"),
    ("Kirish eshigining qulfi buzuq", "defense", "door"),
    ("Bunkerda kalamushlar bor", "defense", "rats"),
    ("Yorug'lik kuniga faqat 6 soat ishlaydi", "energy", "light"),
    ("Zaxiraning yarmi muddati o'tgan", "food", "spoiled"),
    ("Hojatxona bitta va u ham tiqilib qolgan", "tech", "toilet"),
    ("Devorlardan suv sizib turibdi", "tech", "leak"),
    ("Bunker xaritasi yo'q, ba'zi xonalar qulflangan", "know", "map"),
]

# ---------------------------------------------------------------- KASBLAR
# (nom, teglar, ball)
PROFESSIONS = [
    ("Jarroh", ["med"], 3),
    ("Hamshira", ["med"], 2),
    ("Stomatolog", ["med"], 1),
    ("Farmatsevt", ["med", "know"], 2),
    ("Psixolog", ["psy"], 2),
    ("Veterinar", ["med", "food"], 2),
    ("Fermer", ["food"], 3),
    ("Oshpaz", ["food"], 2),
    ("Ovchi", ["food", "defense"], 3),
    ("Baliqchi", ["food"], 2),
    ("Elektrik", ["energy", "tech"], 3),
    ("Santexnik", ["tech"], 2),
    ("Muhandis", ["tech", "energy"], 3),
    ("Avtomexanik", ["tech"], 2),
    ("Quruvchi", ["tech"], 2),
    ("Harbiy ofitser", ["defense"], 3),
    ("Politsiyachi", ["defense"], 2),
    ("Qo'riqchi", ["defense"], 1),
    ("Kimyogar", ["know", "med"], 2),
    ("Biolog", ["know", "food"], 2),
    ("Geolog", ["know"], 1),
    ("Fizik", ["know", "energy"], 2),
    ("O'qituvchi", ["know", "psy"], 1),
    ("Dasturchi", ["tech", "comm"], 1),
    ("Radioinjener", ["comm", "tech"], 2),
    ("Uchuvchi", ["comm"], 0),
    ("Kosmonavt", ["know", "tech"], 1),
    ("Sportchi-trener", ["psy", "defense"], 1),
    ("Yurist", [], -1),
    ("Bankir", [], -2),
    ("Aktyor", ["psy"], 0),
    ("Musiqachi", ["psy"], 0),
    ("Sartarosh", ["psy"], 0),
    ("Fotograf", [], -1),
    ("Jurnalist", ["comm"], 0),
    ("Tarixchi", ["know"], 0),
    ("Bloger (2 mln obunachi)", [], -2),
    ("Professional geymer", [], -2),
    ("Influenser (o'zi shunday deydi)", [], -3),
    ("Kripto-investor", [], -2),
    ("Talaba (3-kurs, qarzdor)", [], -1),
    ("Siyosatchi", [], -2),
    ("Astrolog", [], -2),
    ("Professional uxlovchi", [], -3),
    ("Mim aktyor", ["psy"], -1),
    ("Sommelye (vino tatib ko'ruvchi)", [], -2),
    # O'zbekcha to'plam
    ("Taksichi (Toshkentni ko'zi yumuq biladi)", ["tech"], 0),
    ("Somsapaz", ["food"], 2),
    ("To'y boshlovchisi (tamada)", ["psy"], 0),
    ("Bozor savdogari", ["comm"], 0),
    ("Usta (hamma ishni qiladi, hech biri tugamaydi)", ["tech"], 1),
    ("Paxtakor", ["food"], 1),
    ("To'y qo'shiqchisi", ["psy"], -1),
    ("Novvoy", ["food"], 2),
    ("Qassob", ["food"], 2),
    ("Mahalla raisi", ["psy", "comm"], 0),
    ("Osh pishiruvchi (500 kishilik qozon)", ["food"], 2),
    ("Dorixonachi xola", ["med"], 1),
    ("Qurilish ustasi (brigadir)", ["tech"], 2),
    ("Kelinlar salonida stilist", [], -1),
    ("Mardikor", ["tech"], 1),
    ("Nonvoy-tandirchi", ["food", "energy"], 2),
]

# ---------------------------------------------------------------- SOG'LIQ
# (matn, ball)
HEALTH = [
    ("Mutlaqo sog'lom", 2),
    ("Sportchi qomati, temirdek sog'lom", 3),
    ("Kuchli immunitet, hech qachon kasal bo'lmagan", 2),
    ("Astma (yengil)", -1),
    ("Yong'oqqa allergiya", -1),
    ("Changga kuchli allergiya", -2),
    ("Ko'rish zaif (−5, ko'zoynaksiz hech narsa ko'rmaydi)", -1),
    ("Eshitish zaif", -1),
    ("Qo'li singan (gipsda)", -1),
    ("Oyog'i jarohatlangan, oqsoqlanadi", -2),
    ("Surunkali uyqusizlik", -1),
    ("Qandli diabet (nazoratda)", -2),
    ("Ortiqcha vazn", -1),
    ("Bel og'rig'i", -1),
    ("Doimiy shamollash", -1),
    ("Dengiz kasalligi (liftda ham ko'ngli ayniydi)", 0),
    ("Rang ajratmaydi", 0),
    ("Migren", -1),
    ("Tishi og'riyapti (3 kundan beri)", 0),
    ("Yuqori qon bosimi", -2),
    ("Uyqusida yuradi", -1),
    ("Hiqichoq to'xtamaydi (2 haftadan beri)", 0),
    ("Laktozani hazm qilolmaydi", 0),
    ("Shirinlikka qaramlik", 0),
]

# ---------------------------------------------------------------- HOBBI
HOBBIES = [
    ("Baliq ovi", ["food"], 2),
    ("Ovchilik", ["food", "defense"], 2),
    ("Bog'dorchilik", ["food"], 2),
    ("Shaxmat", ["psy", "know"], 1),
    ("Boks", ["defense"], 1),
    ("Gitara chalish", ["psy"], 1),
    ("Kulinariya", ["food"], 1),
    ("Tikuvchilik", ["tech"], 1),
    ("Turizm va tog'ga chiqish", ["defense"], 1),
    ("Yoga va meditatsiya", ["psy"], 1),
    ("Kompyuter o'yinlari", [], -1),
    ("Radio-havaskorlik", ["comm"], 2),
    ("Duradgorlik", ["tech"], 2),
    ("Birinchi yordam kurslari", ["med"], 2),
    ("Kitob o'qish", ["know", "psy"], 1),
    ("Raqs", ["psy"], 0),
    ("Parkur", [], 0),
    ("Elektronika yig'ish", ["tech", "energy"], 2),
    ("Kamondan otish", ["defense"], 2),
    ("Stand-up komediya", ["psy"], 1),
    ("TikTok uchun raqs videolari", [], -2),
    ("Selfi olish", [], -2),
    ("Kollektsiya: qopqoqlar yig'ish", [], -1),
    ("Seriallar marafoni", [], -1),
    ("Astronomiya", ["know"], 1),
    # O'zbekcha to'plam
    ("Uloq-ko'pkari", ["defense"], 1),
    ("Palov damlash", ["food", "psy"], 2),
    ("Kurash", ["defense"], 1),
    ("Dutor chalish", ["psy"], 1),
    ("Qo'shni bilan choyxonada gurung", ["psy"], 0),
    ("Bedana boqish", ["food"], 2),
    ("Kaptar uchirish", ["comm"], 0),
]

# ---------------------------------------------------------------- FOBIYALAR
# (matn, kalit, ball)
PHOBIAS = [
    ("Klaustrofobiya (yopiq joydan qo'rqadi)", "claustro", -3),
    ("Qorong'ilikdan qo'rqadi", "dark", -2),
    ("Balandlikdan qo'rqadi", "height", 0),
    ("O'rgimchaklardan qo'rqadi", "spider", 0),
    ("Itlardan qo'rqadi", "dog", 0),
    ("Qon ko'rsa hushidan ketadi", "blood", -1),
    ("Olomondan qo'rqadi", "crowd", -1),
    ("Suvdan qo'rqadi", "water", -1),
    ("Ilonlardan qo'rqadi", "snake", 0),
    ("Yolg'izlikdan qo'rqadi", "alone", 0),
    ("Mikroblardan qo'rqadi (kuniga 40 marta qo'l yuvadi)", "germs", -1),
    ("Fobiyasi yo'q", "none", 1),
    ("Tovuqlardan qo'rqadi", "chicken", 0),
    ("Qaynonadan qo'rqadi", "inlaw", 0),
    ("Kalamushlardan qo'rqadi", "rats", -1),
    ("Telefon zaryadi 20% dan tushsa vahimaga tushadi", "battery", -1),
    ("Imtihondan qo'rqadi (hali ham tushida ko'radi)", "exam", 0),
]

# ---------------------------------------------------------------- XARAKTER
TRAITS = [
    ("Xotirjam", "calm", 1),
    ("Tez jahli chiqadi", "angry", -2),
    ("Tug'ma yetakchi", "leader", 2),
    ("Patologik yolg'onchi", "liar", -2),
    ("Hazilkash", "funny", 1),
    ("Dangasa", "lazy", -2),
    ("Mehnatkash", "worker", 2),
    ("Pessimist", "pessimist", -1),
    ("Juda ishonuvchan", "naive", 0),
    ("Ochko'z", "greedy", -2),
    ("Mehribon", "kind", 1),
    ("Gapdon (og'zi yopilmaydi)", "talker", -1),
    ("Tartibli", "neat", 1),
    ("Hasadgo'y", "envy", -1),
    ("Jasur", "brave", 1),
    ("Qo'rqoq", "coward", -1),
    ("Hamma narsaga 'ok' deydi", "ok", 0),
    ("Doim kechikadi", "late", -1),
    ("Xurrak otadi (juda baland)", "snore", -1),
    ("Hamma narsani bilaman deydi", "knowall", -1),
]

# ---------------------------------------------------------------- YUK
LUGGAGE = [
    ("Birinchi yordam sumkasi", ["med"], 2),
    ("Antibiotiklar qutisi", ["med"], 3),
    ("Ov miltig'i va 30 ta o'q", ["defense", "food"], 3),
    ("Urug'lar to'plami (50 tur)", ["food"], 3),
    ("Kichik quyosh paneli", ["energy"], 2),
    ("Ratsiya (2 ta)", ["comm"], 2),
    ("Asboblar qutisi", ["tech"], 2),
    ("Ko'chma suv filtri", ["tech"], 3),
    ("Chodir", [], 0),
    ("10 kg guruch", ["food"], 2),
    ("Gitara", ["psy"], 0),
    ("Bir quti kitob", ["know", "psy"], 1),
    ("Noutbuk (zaryadsiz)", [], -1),
    ("Mushuk", ["psy"], 0),
    ("Bolta", ["defense", "tech"], 1),
    ("Xarita va kompas", ["know"], 1),
    ("Bir yashik konserva", ["food"], 2),
    ("Shaxmat taxtasi", ["psy"], 0),
    ("Oltin zanjir (500 g)", [], -1),
    ("Selfi tayoqcha", [], -2),
    ("Power bank (to'liq)", ["energy"], 1),
    ("Qaynatilgan tuxum (12 ta)", ["food"], 0),
    ("Jonli tovuq", ["food"], 1),
    ("Dumbbell (20 kg)", [], -1),
    ("Karaoke mikrofoni", ["psy"], -1),
    ("Ko'zguli quti (chiroyli, lekin nima uchun?)", [], -2),
    ("Hayot haqida motivatsion kitob", [], -1),
    ("Benzinli generator", ["energy"], 3),
    ("Termos va 3 kg ko'k choy", ["psy"], 1),
    # O'zbekcha to'plam
    ("Qozon (50 litrlik)", ["food"], 1),
    ("3 kg qazi", ["food"], 2),
    ("Ko'rpacha (5 ta)", ["energy"], 1),
    ("10 ta non", ["food"], 1),
    ("Choynak va piyolalar", ["psy"], 0),
    ("Dutor", ["psy"], 0),
    ("Bir qop kartoshka", ["food"], 2),
    ("Bir xalta qurt", ["food"], 1),
    ("Navvot va parvarda", ["psy"], 0),
    ("Bir mashina g'isht (qayerga?)", [], -2),
    ("Dazmol (eski, cho'yan)", ["defense"], 0),
    ("Bir banka achchiq-chuchuk", ["food"], 0),
]

# ---------------------------------------------------------------- FAKTLAR
FACTS = [
    ("3 yil Antarktidada yashagan", ["energy"], 2),
    ("5 ta tilda gapiradi", ["comm"], 1),
    ("Harbiy xizmatni o'tagan", ["defense"], 2),
    ("Bir paytlar qamoqxona oshpazi bo'lgan", ["food"], 1),
    ("Aynan shu bunker qurilishida ishlagan", ["tech", "know"], 3),
    ("Yashirincha millioner", [], -1),
    ("Bolaligida cho'lda adashib, 4 kun yashab qolgan", ["food"], 1),
    ("Uxlayotganda gapiradi (sirlarni ham)", [], -1),
    ("Gipnoz qila oladi", ["psy"], 1),
    ("Qishloqda o'sgan, mol boqishni biladi", ["food"], 2),
    ("Tibbiyot institutidan 3-kursda chiqib ketgan", ["med"], 1),
    ("Avval professional o'g'ri bo'lgan", ["tech"], 0),
    ("Survival shoularni 300 soat ko'rgan", [], 0),
    ("Bir marta zombi filmida statist bo'lgan", [], 0),
    ("Radio orqali dunyoning yarmi bilan tanish", ["comm"], 2),
    ("Kimyo olimpiadasi g'olibi", ["know", "med"], 2),
    ("O'zini kelajakdan kelgan deb hisoblaydi", [], -2),
    ("Harbiy dalada shifokor yordamchisi bo'lgan", ["med", "defense"], 2),
    ("Telefoni bo'lmasa 1 soatda zerikib o'ladi", [], -1),
    ("Hech qachon ovqat pishirmagan, choy ham", [], -1),
    ("Uyidan 10 yil chiqmagan (karantin chempioni)", ["psy"], 1),
    # O'zbekcha to'plam
    ("200 ta to'yda osh tarqatgan", ["food"], 1),
    ("Har qanday 'Nexia'ni ko'r holda tuzata oladi", ["tech"], 2),
    ("Mahalladagi hamma janjallarni yarashtirgan", ["psy"], 2),
    ("Bozorda narx tushirishda tengsiz", ["comm"], 0),
    ("Buvisidan o'tgan xalq tabobatini biladi", ["med"], 1),
    ("Choyxonada 40 yil gurung qilgan", ["psy"], 0),
    ("Qudalarni 15 daqiqada kelishtira oladi", ["psy", "comm"], 1),
]

# ---------------------------------------------------------------- MAXSUS KARTALAR
# kalit: (nom, tavsif, nishon kerakmi: None | "other" | "any")
ACTIONS = {
    "immunitet": ("Immunitet", "Shu raundda sizga berilgan ovozlar hisoblanmaydi.", None),
    "ikki_ovoz": ("Ikki ovoz", "Shu raundda ovozingiz 2 ga teng bo'ladi.", None),
    "veto": ("Veto", "Tanlangan o'yinchining shu raunddagi ovozi bekor qilinadi.", "other"),
    "josus": ("Josus", "Tanlangan o'yinchining bitta yopiq kartasini yashirincha ko'rasiz.", "other"),
    "fosh": ("Fosh qilish", "Tanlangan o'yinchining bitta yopiq kartasi hozir hammaga ochiladi.", "other"),
    "shifokor": ("Shifokor", "Tanlangan o'yinchining sog'lig'i 'Mutlaqo sog'lom'ga almashadi.", "any"),
    "yangi_kasb": ("Yangi kasb", "Kasbingiz tasodifiy yangi kasbga almashadi.", None),
    "tamirchi": ("Ta'mirchi", "Bunker muammosi tuzatiladi.", None),
    "sabotaj": ("Sabotaj", "Bunker oziq-ovqat zaxirasi 3 oyga kamayadi.", None),
    "topilma": ("Topilma", "Omborda yashirin zaxira topildi: +4 oy oziq-ovqat.", None),
    "hamma_ochsin": ("Hamma ochsin", "Keyingi raundda hamma 2 tadan karta ochadi.", None),
    "joy": ("Qo'shimcha joy", "Bunkerga 1 ta qo'shimcha o'rin qo'shiladi.", None),
}
# tasodifiy tanlash og'irliklari (joy — juda kamyob)
ACTION_WEIGHTS = {
    "immunitet": 6, "ikki_ovoz": 8, "veto": 8, "josus": 9, "fosh": 9, "shifokor": 6,
    "yangi_kasb": 7, "tamirchi": 6, "sabotaj": 6, "topilma": 6, "hamma_ochsin": 6, "joy": 2,
}

# ---------------------------------------------------------------- TASHQARIDAGILAR TAQDIRI
OUTSIDE_FATES_BAD = [
    "{name} tashqarida 3 kun yurdi, keyin bunker eshigini taqillatdi. Hech kim ochmadi. Hozir ham taqillatayotgan bo'lishi mumkin.",
    "{name} yaqin atrofdagi do'kondan chips topdi va baxtli yashadi. 2 hafta.",
    "{name} boshqa omon qolganlar guruhiga qo'shildi va ularning yetakchisiga aylandi. Afsuski, guruh 2 kishidan iborat edi.",
    "{name} tashqarida signal izlab 40 km yurdi. Signal topildi, lekin internet hali ham yo'q edi.",
    "{name} bunker yonida chodir tikib, har kuni ventilyatsiya teshigidan maslahat berib turdi.",
    "{name} o'zini qahramon deb e'lon qildi va dunyoni qutqarishga ketdi. Qaytmadi.",
    "{name} tashlab ketilgan to'yxonada yashay boshladi. Har kuni o'ziga o'zi tost aytadi.",
    "{name} birinchi kuniyoq tashqi dunyoga moslashdi: endi yovvoyi itlar uning oilasi.",
]
OUTSIDE_FATES_GOOD = [
    "{name} tashqarida o'z bunkerini topdi — kattaroq, issiqroq va Wi-Fi bilan. U sizlardan ham yaxshi yashadi.",
    "{name} tog'larda tirik qolganlar qishlog'ini topdi va u yerda hurmatli oqsoqolga aylandi.",
    "{name} tashlab ketilgan supermarketni egalladi. 2 yil davomida faqat shokolad yedi va bunkerdagilardan sog'lomroq chiqdi.",
]

# ---------------------------------------------------------------- QOIDALAR MATNI
RULES_TEXT = (
    "<b>📖 Bunker — qisqa qoidalar</b>\n\n"
    "Dunyoda falokat yuz berdi. Omon qolishning yagona yo'li — bunker, lekin unda joy hammaga yetmaydi.\n\n"
    "<b>1.</b> Har kimga yashirin xarakter beriladi: kasb, yosh, sog'liq, hobbi, fobiya, xarakter, yuk va qo'shimcha fakt. Shuningdek, bitta maxsus karta.\n\n"
    "<b>2.</b> Kartalar navbatma-navbat ochiladi (kim birinchi qo'shilgan bo'lsa, o'sha boshlaydi). 1-raundda hamma kasbini ochadi. Keyingi raundlarda birinchi o'yinchi qaysi turdagi kartani ochsa, qolganlar ham shu turni ochadi. Karta ochilgach, egasi qisqa gapiradi.\n\n"
    "<b>3.</b> Keyin muhokama: nega aynan siz bunkerga kirishingiz kerakligini isbotlang. Yopiq kartalaringiz haqida blef qilish mumkin, ochilganlari haqida yolg'on gapirib bo'lmaydi.\n\n"
    "<b>4.</b> Ovoz berish: eng ko'p ovoz olgan o'yinchi chiqarib yuboriladi. Ovozlar teng bo'lsa — himoya so'zi va qayta ovoz, yana teng bo'lsa — zar 🎲.\n\n"
    "<b>5.</b> Bunkerga 4–10 o'yinchida 2 kishi, 11–14 o'yinchida 3 kishi kiradi.\n\n"
    "<b>6.</b> Oxirida bot jamoani falokatga qarab baholaydi va omon qolgan-qolmaganingizni hikoya qilib beradi. Foydasiz jamoa bunkerda ham halok bo'lishi mumkin!\n\n"
    "<i>Guruhda: botni guruhga qo'shing va /bunker yozing.\n"
    "Guruhsiz: botga shaxsiyda /bunker yozing va havolani do'stlaringizga yuboring.</i>"
)
