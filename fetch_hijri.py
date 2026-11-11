# يقرأ إعلانات بداية الأشهر الهجرية (دائرة الإفتاء الأردنية) من عناوين الأخبار الأردنية ويكتب hijri.json
# أي فشل لا يوقف التحديث: الصفحة تعود تلقائيًا إلى تقويم أم القرى.
import json, math, re, datetime, email.utils, urllib.request
import xml.etree.ElementTree as ET

FEEDS = ["https://www.almamlakatv.com/rss.xml", "https://alghad.com/rss"]
MONTH_AR = {1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الآخر", 5: "جمادى الأولى", 6: "جمادى الآخرة",
            7: "رجب", 8: "شعبان", 9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"}
NAMES = {1: ["محرم"], 2: ["صفر"], 3: ["ربيع الاول"], 4: ["ربيع الاخر", "ربيع الثاني"],
         5: ["جمادى الاولى", "جمادي الاولي"], 6: ["جمادى الاخره", "جمادى الثانيه", "جمادى الاخر", "جمادي الاخره"],
         7: ["رجب"], 8: ["شعبان"], 9: ["رمضان"], 10: ["شوال"], 11: ["ذو القعده", "ذي القعده"], 12: ["ذو الحجه", "ذي الحجه"]}
WEEKDAYS = {"الاثنين": 0, "الثلاثاء": 1, "الاربعاء": 2, "الخميس": 3, "الجمعه": 4, "السبت": 5, "الاحد": 6}

def norm(s):
    s = re.sub(r"[ً-ٰٟـ]", "", s)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه")):
        s = s.replace(a, b)
    s = s.replace("جمادي", "جمادى").replace("الاولي", "الاولى")
    return re.sub(r"\s+", " ", s).strip()

def civil_start(y, m):
    """بداية الشهر بالتقويم الهجري الحسابي (تقدير) لاستعمالها في التحقق فقط."""
    jd = 1 + math.ceil(29.5 * (m - 1)) + (y - 1) * 354 + (3 + 11 * y) // 30 + 1948439.5 - 1
    return datetime.date.fromordinal(int(jd + 0.5) - 1721425)

def parse_title(title, pub):
    """pub: تاريخ النشر بتوقيت عمّان. تعيد (التاريخ الميلادي، رقم الشهر، السنة الهجرية) أو None."""
    t = norm(title)
    if not ("افتاء" in t or "مفتي" in t):
        return None
    if not re.search(r"غره|اول ايام|مطلع|اول يوم", t):
        return None
    month = None
    if "عيد الفطر" in t:
        month = 10
    else:
        best = 0
        for m, names in NAMES.items():
            for nm in names:
                if nm in t and len(nm) > best:
                    month, best = m, len(nm)
    if not month:
        return None
    day = None
    if "غدا" in t:
        day = pub + datetime.timedelta(days=1)
    elif "اليوم" in t:
        day = pub
    else:
        for w, i in WEEKDAYS.items():
            if w in t:
                day = pub + datetime.timedelta(days=(i - pub.weekday()) % 7)
                break
    if not day:
        return None
    for y in range(1446, 1455):                      # تحقق: يجب أن يقارب التقدير الحسابي (±2 يوم)
        if abs((civil_start(y, month) - day).days) <= 2:
            return day, month, y
    return None

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (home-screen bot)"})
    return urllib.request.urlopen(req, timeout=25).read()

def main():
    try:
        old = json.load(open("hijri.json", encoding="utf-8")).get("starts", [])
    except Exception:
        old = []
    found = {(e["y"], e["mn"]): e for e in old if "mn" in e}
    for url in FEEDS:
        try:
            root = ET.fromstring(fetch(url))
            for it in root.iter("item"):
                title = (it.findtext("title") or "").strip()
                pd = it.findtext("pubDate")
                if not title or not pd:
                    continue
                dt = email.utils.parsedate_to_datetime(pd)
                pub = (dt.astimezone(datetime.timezone.utc) + datetime.timedelta(hours=3)).date()
                r = parse_title(title, pub)
                if r:
                    d, m, y = r
                    found[(y, m)] = {"g": d.isoformat(), "m": MONTH_AR[m], "y": y, "mn": m, "src": title[:80]}
        except Exception as e:
            print("hijri feed failed:", url, type(e).__name__)
    starts = sorted(found.values(), key=lambda e: e["g"])[-24:]
    out = json.dumps({"starts": starts}, ensure_ascii=False, indent=1)
    try:
        if open("hijri.json", encoding="utf-8").read() == out:
            return
    except Exception:
        pass
    open("hijri.json", "w", encoding="utf-8").write(out)

if __name__ == "__main__":
    main()
