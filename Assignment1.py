import urllib.request
import re
import json
from html import unescape
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

pages = [
    "https://time.com/section/politics/",
    "https://time.com/section/world/",
    "https://time.com/section/health/",
    "https://time.com/section/climate/",
    "https://time.com/section/science/",
    "https://time.com/section/entertainment/",
    "https://time.com/section/ideas/",
]

def getPage(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode('utf-8', errors='ignore')

def chngDate(date):
    dateFmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in dateFmts:
        try:
            return datetime.strptime(date, fmt)
        except Exception:
            continue
    return None
    

def getArticle(link, res, lock):

    arti = getPage(link)
    real_Title = re.search(r'<title>(.*?)</title>', arti, re.IGNORECASE | re.DOTALL)
    if real_Title:
        title = unescape(real_Title.group(1)).strip()
        title = title.removesuffix(" - TIME").strip()
    else:
        title = "No title found"

    time = re.search(r'<time[^>]*datetime=["\']([^"\']+)["\'][^>]*>', arti, re.IGNORECASE)
    if not time:
        time2 = re.search(r'<time[^>]*>(.*?)</time>', arti, re.IGNORECASE | re.DOTALL)
        det_time = unescape(time2.group(1)).strip() if time2 else ""
        finalTime = chngDate(det_time) or None
    else:
        finalTime = chngDate(time.group(1).strip())

    with lock:
        res.append({"title": title, "link": link.rstrip('\\'), "finalTime": finalTime})

def latestArti(url, numArticles=6):
    articles = []
    html = getPage(url)
    patt = r'https://time\.com/\d{7}(?:/[^\s"<>]*)?'
    match = re.findall(patt, html)
    seen = set()
    links = []
    for link in match:
        if link not in seen:
            seen.add(link)
            links.append(link)
    links = links[:numArticles]
    threads = []
    lock = threading.Lock()
    for link in links:
        t = threading.Thread(target=getArticle, args=(link, articles, lock))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return articles


articles = []
threads = []
lock = threading.Lock()

def sections(page, bucket, lock):
    results = latestArti(page, 6)
    with lock:
        bucket.extend(results)

for page in pages:
    t = threading.Thread(target=sections, args=(page, articles, lock))
    t.start()
    threads.append(t)
for t in threads:
    t.join()

def NormTime(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

unique = []
seenLinks = set()
for article in articles:
    link = article.get("link")
    if link not in seenLinks:
        seenLinks.add(link)
        unique.append(article)

validArticles = [a for a in unique if isinstance(a.get("finalTime"), datetime)]

for article in validArticles:
    article["normTime"] = NormTime(article["finalTime"])

sortArti = sorted(
    validArticles, 
    key=lambda x: x["normTime"], 
    reverse=True
)

finalVal = sortArti[:6]

for article in finalVal:
    article.pop("finalTime", None)
    if "normTime" in article:
        del article["normTime"]

finalJson = json.dumps(finalVal, indent=2, ensure_ascii=False)

print(finalJson)

def getRequest(self):
    if self.path == "/getTimeStories":
        try:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(finalJson.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    else:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not Found')

def server(port= 8080):
    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        pass

    SimpleHTTPRequestHandler.do_GET = getRequest
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting server on port {port}")
    print(f'Access the API at: http://localhost:{port}/getTimeStories')
    httpd.serve_forever()

server(8080)

