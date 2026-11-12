import json, re, datetime, urllib.request, urllib.parse, xml.etree.ElementTree as ET

# ---------- المصادر: لكل مصدر روابط خلاصة معروفة وصفحات رئيسية يُكتشف منها الرابط تلقائيًا ----------
SOURCES = [
    {"name": "المملكة", "feeds": ["https://www.almamlakatv.com/rss.xml"], "homes": [], "local": True},
    {"name": "الغد", "feeds": ["https://alghad.com/rss"], "homes": [], "local": True},
    {"name": "التلفزيون العربي", "feeds": ["https://www.alaraby.tv/feed"], "homes": []},
    {"name": "الجزيرة نت", "feeds": ["https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9"], "homes": []},
    {"name": "بي بي سي عربي", "feeds": ["https://feeds.bbci.co.uk/arabic/rss.xml"], "homes": []},
]
GUESS = ["/feed", "/feed/", "/rss", "/rss.xml", "/rss/", "/feeds/rss.xml", "/rss.php", "/?feed=rss2"]
PER_SOURCE = 3
MAX_LEN = 100

# ---------- فلترة العناوين: أخبار سياسية واقتصادية واجتماعية مهمة ومختصرة ----------
# يُحذف العنوان إن فيه كلمة من EXCLUDE أو كان سؤالًا أو طويلًا، ثم لا يُقبل إلا إن فيه كلمة من INCLUDE.
EXCLUDE = ["نشاط ممتع", "طفلك", "وصفة", "الأبراج", "حظك", 
           "فنان", "مسلسل", "فيلم", "أغنية", "موضة", "رجيم", "حمية", "طبخ", "آيفون", "ألعاب", "حصالة",
           "عيد ميلاد", "زفاف", "مهرجان", "نصائح", "فوائد", "أسرار", "أفضل", "طرق", "اكتشف", "تعرف على",
           "دراسة", "كل ما تحتاج", "بالأرقام", "بالخرائط", "الذكاء الاصطناعي", "تقرير:", "شهادات", "كيف", "لماذا",
           "ماذا", "هل ", "؟", "?", "إليك", "أبرز ", "قصة ", "حكاية", "في صور", "فيديو"]
INCLUDE = ["الحكومة", "الوزراء", "الرئيس", "وزير", "وزارة", "مجلس", "النواب", "الأعيان", "الملك", "ولي العهد", "سياس",
           "برلمان", "انتخاب", "اتفاق", "مفاوضات", "هدنة", "حرب", "غارات", "قصف", "عدوان", "غزة",
           "فلسطين", "الضفة", "القدس", "الأقصى", "إسرائيل", "الاحتلال", "سوريا", "لبنان", "العراق", "إيران",
           "واشنطن", "الأمم المتحدة", "مجلس الأمن", "عقوبات", "الجيش", "عاجل", "الأردن", "أردني",
           "اقتصاد", "أسعار", "سعر", "الدينار", "الدولار", "الذهب", "النفط", "موازنة", "ضريبة", "الضمان",
           "بنك", "البنك", "تضخم", "بطالة", "رواتب", "أجور", "استثمار", "الغاز", "الكهرباء", "المياه",
           "الدين", "ديون", "صادرات", "بورصة", "الأسواق",
           "تعليم", "الجامعات", "التوجيهي", "المستشفى", "نقابة", "الفقر", "السكن", "قانون",
           "القضاء", "محكمة", "فساد", "الأمن العام", "الدفاع المدني", "حريق", "فيضان"]

# ---- استبعاد عام: الصحة والحياة والنصائح ----
EXCLUDE += ["العزاء", "التعزية", "تعزية", "نعي", "تنعى", "التهنئة", "تهنئة", "يهنئ", "تهنئ", "مسارين", "مساري", "مسارات جديدة", "النقل البري", "تطلق مسار", "الصحة", "صحي", "صحية", "مرض", "أمراض", "علاج", "طبيب", "سرطان", "مستشفى", "المستشفى", "غذاء", "تغذية",
            "دواء", "لقاح", "فيروس", "الحياة", "نمط", "أسلوب", "نصيحة", "تحذير من تناول", "الطقس", "حالة الطقس"]
INCLUDE = [w for w in INCLUDE if w not in ("المستشفى",)]

# ---- المصادر المحلية: أخبار أردنية مهمة فقط ----
LOCAL = ["الأردن", "الأردني", "الأردنية", "عمّان", "عمان", "الحكومة", "النواب", "الأعيان", "الملك", "ولي العهد",
         "وزارة", "وزير", "الوزراء", "مجلس", "الضمان", "الدينار", "أسعار", "المحروقات", "البنزين", "الكهرباء",
         "المياه", "الأمن العام", "الدفاع المدني", "التوجيهي", "الجامعات", "التعليم", "الموازنة", "الضريبة",
         "البطالة", "الرواتب", "السيول", "فيضان", "حريق", "القضاء", "محكمة", "فساد", "نقابة", "قانون", "البنك المركزي",
         "العقبة", "إربد", "الزرقاء", "الكرك", "معان", "السلط", "مأدبا", "المفرق", "جرش", "عجلون", "الطفيلة"]
WORLD = ["إسرائيل", "إسرائيلية", "نتنياهو", "ترامب", "ترمب", "إيران", "البرازيل", "لولا", "أميركا", "أمريكا", "واشنطن",
         "اليمن", "سوريا", "السورية", "لبنان", "العراق", "غزة", "فلسطين", "الضفة", "الاحتلال", "روسيا", "أوكرانيا", "الصين"]

# الرياضة: تُستبعد كلها إلا الأحداث المفصلية والنهائيات وأخبار ريال مدريد
SPORT = ["الرياضة", "رياضي", "رياضية", "كرة", "الدوري", "مباراة", "مباريات", "المنتخب", "نادي", "هدف", "هدفا", "فوز", "فاز", "يفوز",
         "تعادل", "هزيمة", "يهزم", "بطولة", "كأس", "لاعب", "مدرب", "تدريب", "ملعب", "الأولمبي", "ميركاتو", "انتقال", "يضم", "يتعاقد",
         "برشلونة", "ليفربول", "مانشستر", "بايرن", "يوفنتوس", "ميلان", "إنتر", "الهلال", "النصر", "الأهلي", "الزمالك", "الوحدات", "الفيصلي",
         "ريال مدريد", "الريال", "ميسي", "رونالدو", "صلاح", "الفيفا", "الاتحاد الدولي", "تنس", "غولف", "فورمولا", "سباق"]
SPORT_KEEP = ["ريال مدريد", "الريال", "نهائي", "النهائي", "النهائيات", "نصف النهائي", "ربع النهائي", "كأس العالم", "كأس أمم", "كأس آسيا",
              "اليورو", "كوبا أمريكا", "الأولمبياد", "الألعاب الأولمبية", "التتويج", "يتوج", "يتوّج", "المتوج", "دوري أبطال", "تأهل", "يتأهل", "التصفيات"]

def is_sport(t):
    return any(w in t for w in SPORT)

def important(t, local=False):
    if len(t) > MAX_LEN or any(w in t for w in EXCLUDE):
        return False
    if is_sport(t):
        return any(w in t for w in SPORT_KEEP)
    if local:
        jo = any(w in t for w in ("الأردن", "الأردني", "الأردنية", "عمّان"))
        if any(w in t for w in WORLD) and not jo:
            return False
        return any(w in t for w in LOCAL)
    return any(w in t for w in INCLUDE)

def norm(t):
    return re.sub(r"[^\u0600-\u06FF0-9a-zA-Z]", "", t)[:35]

def get(url, limit=3000000):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; HomeScreenBot)", "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=15).read(limit)

def titles_of(data):
    root = ET.fromstring(data)
    out = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("item", "entry"):
            for ch in el:
                if ch.tag.split("}")[-1] == "title" and ch.text:
                    t = re.sub(r"\s+", " ", ch.text).strip()
                    if t:
                        out.append(t)
    return out

def discover(home):
    cands = []
    try:
        html = get(home, 400000).decode("utf-8", "ignore")
        for m in re.finditer(r"<link[^>]+type=[\"']application/(?:rss|atom)\+xml[\"'][^>]*>", html, re.I):
            h = re.search(r"href=[\"']([^\"']+)", m.group(0))
            if h:
                cands.append(urllib.parse.urljoin(home, h.group(1)))
        for m in re.finditer(r"href=[\"']([^\"']*(?:rss|feed)[^\"']*)", html, re.I):
            cands.append(urllib.parse.urljoin(home, m.group(1)))
    except Exception:
        pass
    cands += [home.rstrip("/") + g for g in GUESS]
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c); out.append(c)
    return out[:12]

status, lists = [], []
for s in SOURCES:
    cands = list(s["feeds"])
    for h in s["homes"]:
        cands += discover(h)
    used, raw, err = None, [], []
    for url in cands[:16]:
        try:
            ts = titles_of(get(url))
            if len(ts) >= 3:
                used, raw = url, ts
                break
            err.append("few:" + url)
        except Exception as e:
            err.append(type(e).__name__ + ":" + url)
    kept = [t for t in raw if important(t, s.get("local"))][:PER_SOURCE]
    lists.append([{"src": s["name"], "title": t} for t in kept])
    status.append({"source": s["name"], "feed": used, "raw": len(raw), "kept": len(kept), "errors": err[:6]})
    print("ok" if used else "fail", s["name"], len(raw), len(kept))

merged, seen_t = [], set()
for i in range(PER_SOURCE):
    for lst in lists:
        if i < len(lst):
            k = norm(lst[i]["title"])
            if k not in seen_t:
                seen_t.add(k)
                merged.append(lst[i])

now = datetime.datetime.utcnow().isoformat() + "Z"
with open("status.json", "w", encoding="utf-8") as f:
    json.dump({"updated": now, "sources": status}, f, ensure_ascii=False, indent=1)
if merged:
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now, "items": merged}, f, ensure_ascii=False)
