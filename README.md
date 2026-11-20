# 🏚 Bunker bot — joylash yo'riqnomasi

Bu yerdagi fayllar alohida Telegram bot uchun: guruh rejimi va guruhsiz xona rejimi bor. Bot 24/7 ishlashi uchun avvalgi botingizdagi sxemani ishlatamiz: **GitHub → Render (bepul) → UptimeRobot**. O'yinlarni saqlash uchun Upstash ham ulanadi.

## 1. GitHub
1. GitHub'da yangi repo yarating, nomi masalan `bunker-bot`.
2. **Add file → Upload files** ni bosing va ushbu papkadagi barcha fayllarni yuklang:
   `bot.py, data.py, game.py, render.py, epilog.py, storage.py, requirements.txt, README.md`
3. **Commit changes** ni bosing.

## 2. Render
1. render.com → **New → Web Service** → `bunker-bot` reposini tanlang.
2. Sozlamalar:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance type:** Free
3. **Environment Variables** bo'limiga quyidagilarni qo'shing:

| Kalit | Qiymat |
|---|---|
| `BOT_TOKEN` | BotFather bergan yangi bot tokeni |
| `REDIS_URL` | Upstash'dagi Redis manzili (pastda) |
| `PYTHON_VERSION` | `3.12.7` |

4. **Create Web Service** ni bosing. Log'da `Health server` va `Start polling` yozuvlari chiqsa, bot ishlayapti.

### REDIS_URL qayerdan olinadi
Upstash → bazangizni oching → **Connect** → **TCP / redis-cli** bo'limidagi `rediss://default:...@...upstash.io:6379` ko'rinishidagi manzilni oling. Eski bot ishlatayotgan bazani ham ishlatsa bo'ladi: Bunker o'z ma'lumotlarini `bunker:` prefiksi bilan saqlaydi, eski bot ma'lumotlariga tegmaydi.
`REDIS_URL` qo'shilmasa ham bot ishlaydi, faqat server qayta ishga tushganda davom etayotgan o'yinlar va statistika o'chib ketadi.

## 3. UptimeRobot
Yangi monitor qo'shing: **HTTP(s)**, manzili Render bergan `https://bunker-bot-xxxx.onrender.com`, interval 5 daqiqa. Shunda bepul server uxlab qolmaydi.

## 4. BotFather (bir martalik)
- `/setdescription` — masalan: *"Do'stlar bilan Bunker o'yini. Falokat, bunker va faqat bir nechta joy!"*
- Guruhda bot o'yin taxtasini pin qilishi uchun uni **admin** qiling (faqat "Pin messages" huquqi yetadi). Admin qilinmasa ham o'yin ishlayveradi, faqat taxta pin bo'lmaydi.

## Qanday o'ynaladi
- **Guruhda:** botni guruhga qo'shing va `/bunker` yozing. O'yinchilar "➕ Qo'shilish"ni bosadi. Bot hali shaxsiyda ochilmagan bo'lsa, tugma avval botni ochadi. Keyin xost "▶️ Boshlash"ni bosadi.
- **Guruhsiz:** botga shaxsiyda `/bunker` yozing yoki "🏠 Xona yaratish"ni bosing va havolani do'stlaringizga yuboring. Muhokama bot orqali bo'ladi: siz yozgan xabarni bot boshqa o'yinchilarga uzatadi.

Buyruqlar: `/bunker` · `/qoidalar` · `/kartalarim` · `/profil` · `/top` · `/chiqish` · `/stop`

## Kartalarni tahrirlash
Barcha kartalar `data.py` faylida. Yangi kasb, yuk yoki falokat qo'shish uchun kerakli ro'yxatga yangi qator yozing va faylni GitHub'ga qayta yuklang. Render botni avtomatik yangilaydi.
