"""
SOLITONKIT  MK III  FINAL  v2
══════════════════════════════════════════════════════════════
  Keyword Extractor   · Serper.dev API
  On-Page SEO Crawler · BeautifulSoup
  PageSpeed Checker   · Google PSI v5
  Keyword Density     · BeautifulSoup + smart tokeniser
  Schema Generator    · Pure Python

  Built by : Shak  (solidsman)
  Version  : MK III Final v2
  Python   : 3.8+
  Install  : pip install requests beautifulsoup4 lxml pillow

  FIXES v2:
  - Crawler: @type list crash (unhashable type: 'list') — fixed
  - Splash: panel overflow & animation math — fixed
  - Splash: boot log text no longer overflows panels — fixed
  - Splash: right panel text clipped within bounds — fixed
  - PageSpeed: fully responsive card layout — fixed
  - PageSpeed: opportunity text uses grid + wraplength — fixed
  - PageSpeed: larger donut ring, better metrics display — fixed
  - Nav icons: replaced K/C/P/D/S with Unicode symbols — fixed
  - Hreflang & nofollow rel list handling — fixed
  - Responsive desktop sizing — fixed
══════════════════════════════════════════════════════════════
"""

import csv, json, math, os, re, sys, threading, time, webbrowser, tkinter as tk
from collections import Counter
from datetime import date
from tkinter import ttk, filedialog, messagebox, scrolledtext
from urllib.parse import urlparse, urljoin

try:
    from PIL import Image as PILImage, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as _ie:
    _r = tk.Tk(); _r.withdraw()
    messagebox.showerror("Missing packages",
        f"Required package not found:\n\n  {_ie}\n\n"
        "Run:\n  pip install requests beautifulsoup4 lxml pillow\nThen relaunch.")
    sys.exit(1)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
VERSION   = "MK III"
APP_TITLE = f"SOLITONKIT  {VERSION}"
TODAY     = date.today().isoformat()

def _app_dir():
    return (os.path.dirname(sys.executable) if getattr(sys,"frozen",False)
            else os.path.dirname(os.path.abspath(__file__)))

APP_DIR     = _app_dir()
CONFIG_FILE = os.path.join(APP_DIR,"soliton_config.json")
FAVICON     = os.path.join(APP_DIR,"favicon.ico")
LOGO_FILE   = os.path.join(APP_DIR,"logo.png")

DEFAULT_CFG = {
    "serper_api":"","pagespeed_api":"","country":"in","language":"en",
    "strategy":"Both","kw_last":"","ps_last_url":"https://",
    "crawl_last":"https://","density_url":"https://","density_kw":"",
}

def cfg_load():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE,"r",encoding="utf-8") as f:
                return {**DEFAULT_CFG,**json.load(f)}
        except: pass
    return dict(DEFAULT_CFG)

def cfg_save(c):
    try:
        with open(CONFIG_FILE,"w",encoding="utf-8") as f:
            json.dump(c,f,indent=2)
    except: pass

# ─── PALETTE ──────────────────────────────────────────────────────────────────
BG      = "#010A14"
BG2     = "#020D1C"
BG3     = "#041525"
BG4     = "#030F1E"
BG5     = "#050C18"
HDRBG   = "#00060F"
SIDEBAR = "#00080F"
SELBG   = "#001E3A"
SELHOV  = "#00152A"
BORDER  = "#071828"
BORDER2 = "#0B2038"
ACCENT  = "#00AAFF"
ACCENT2 = "#005599"
ACCENT3 = "#003A7A"
ADIM    = "#001833"
FG      = "#A8D8FF"
FG2     = "#3A6E90"
FG3     = "#163250"
SUCCESS = "#00EE88"
WARNING = "#F0A000"
DANGER  = "#FF2244"

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
COUNTRIES = [
    ("Global",""),("Sri Lanka","lk"),("India","in"),("USA","us"),
    ("UK","gb"),("Australia","au"),("Canada","ca"),("Singapore","sg"),
    ("UAE","ae"),("Germany","de"),("France","fr"),("Japan","jp"),("Brazil","br"),
]
C_LABELS  = [c[0] for c in COUNTRIES]
C_TO_CODE = {c[0]:c[1] for c in COUNTRIES}
C_TO_LBL  = {c[1]:c[0] for c in COUNTRIES}
LANGUAGES  = ["en","si","hi","fr","de","es","ar","ja","pt","zh","ta","ml"]

SOURCE_ORDER = {
    "Seed Keyword":0,"People Also Ask":1,"Related Search":2,
    "Organic Title":3,"Featured Snippet":4,"Knowledge Graph":5,
    "Top Stories":6,"Sitelink":7,
}

_STOP = {"next","previous","more","google","sign in","sign up","settings",
         "home","menu","search","click here","read more","learn more",
         "see more","show more","view all"}

DENSITY_STOP = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "can","this","that","these","those","i","we","you","he","she","it",
    "they","my","our","your","his","her","its","their","what","which",
    "who","whom","when","where","why","how","all","both","each","few",
    "more","most","other","some","such","no","not","only","same","so",
    "than","too","very","just","about","above","after","again","against",
    "also","any","as","because","before","between","during","here","if",
    "into","itself","me","much","new","now","out","own","over","s","t",
    "re","ve","ll","d","m","there","then","them","through","under","until",
    "up","us","while","within","without","yet","am","across","along",
    "already","page","site","website","click","get","use","one","two",
    "three","four","five","six","seven","eight","nine","ten","www","com",
    "http","https","html","css","js","px","em","en","de","el","al","la",
    "le","les","du","des","un","une","dont","dans","sur","par","qu",
}

SERPER_URL = "https://google.serper.dev/search"
PS_URL     = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
TIMEOUT    = 60
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# ─── TTK STYLES ───────────────────────────────────────────────────────────────
def _apply_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    for k,v in [
        ("*TCombobox*Listbox.background",       BG3),
        ("*TCombobox*Listbox.foreground",       FG),
        ("*TCombobox*Listbox.selectBackground", ACCENT3),
        ("*TCombobox*Listbox.selectForeground", "#FFFFFF"),
        ("*TCombobox*Listbox.borderWidth",      "0"),
        ("*TCombobox*Listbox.relief",           "flat"),
    ]:
        root.option_add(k,v)

    s.configure("T.Treeview",background=BG3,foreground=FG,rowheight=26,
                fieldbackground=BG3,font=("Consolas",9),
                borderwidth=0,relief="flat",bordercolor=BG3)
    s.configure("T.Treeview.Heading",background=BG2,foreground=ACCENT,
                font=("Consolas",9,"bold"),relief="flat",
                borderwidth=0,darkcolor=BG2,lightcolor=BG2)
    s.map("T.Treeview",
          background=[("selected",ACCENT3)],
          foreground=[("selected","#FFFFFF")])

    for orient in ("Vertical","Horizontal"):
        s.configure(f"T.{orient}.TScrollbar",
                    background=BG2,troughcolor=BG3,borderwidth=0,
                    arrowcolor=FG3,relief="flat",darkcolor=BG2,lightcolor=BG2)
        s.map(f"T.{orient}.TScrollbar",
              background=[("active",BORDER2)],
              arrowcolor=[("active",ACCENT)])

    s.configure("T.Horizontal.TProgressbar",
                troughcolor=BG2,background=ACCENT,borderwidth=0,
                thickness=2,relief="flat",darkcolor=ACCENT,lightcolor=ACCENT)

    s.configure("TCombobox",fieldbackground=BG3,background=BG3,foreground=FG,
                selectbackground=ACCENT3,selectforeground="#FFFFFF",
                arrowcolor=ACCENT,borderwidth=0,relief="flat",
                darkcolor=BG3,lightcolor=BG3,insertcolor=ACCENT)
    s.map("TCombobox",
          fieldbackground=[("readonly",BG3),("disabled",BG4)],
          background=[("readonly",BG3),("active",BG3)],
          foreground=[("readonly",FG),("disabled",FG3)],
          selectbackground=[("readonly",ACCENT3)],
          bordercolor=[("focus",ACCENT),("!focus",BORDER)])

    s.configure("TCheckbutton",background=BG2,foreground=FG2,
                focuscolor=BG2,font=("Consolas",9))
    s.map("TCheckbutton",
          background=[("active",BG2)],
          foreground=[("active",ACCENT)],
          indicatorcolor=[("selected",ACCENT),("!selected",BG3)])

# ─── WIDGETS ──────────────────────────────────────────────────────────────────
def _lbl(parent,text,size=9,fg=None,bold=False):
    return tk.Label(parent,text=text,fg=fg or FG2,bg=parent.cget("bg"),
                    font=("Segoe UI",size,"bold" if bold else "normal"))

def _entry(parent,default="",width=28):
    e=tk.Entry(parent,width=width,font=("Consolas",9),
               bg=BG3,fg=FG,insertbackground=ACCENT,
               relief="flat",bd=0,
               highlightthickness=1,highlightbackground=BORDER,
               highlightcolor=ACCENT,selectbackground=ACCENT3,
               selectforeground="#FFFFFF",disabledbackground=BG4,
               disabledforeground=FG3)
    if default: e.insert(0,default)
    return e

def _btn(parent,text,cmd,bg=None,width=None,small=False):
    bg=bg or ACCENT2
    hov=(ACCENT    if bg==ACCENT2   else
         ACCENT3   if bg==BG3       else
         "#5A1020" if bg=="#3A0A0A" else
         "#076B4B" if bg=="#054D36" else
         "#001628" if bg==SIDEBAR   else ADIM)
    font=("Segoe UI",8,"bold") if small else ("Segoe UI",9,"bold")
    px=10 if small else 14
    py=4  if small else 7
    b=tk.Button(parent,text=text,command=cmd,
                bg=bg,fg="#FFFFFF",font=font,
                relief="flat",bd=0,padx=px,pady=py,cursor="hand2",
                activebackground=hov,activeforeground="#FFFFFF")
    if width: b.configure(width=width)
    b.bind("<Enter>",lambda _,b=b,h=hov:b.configure(bg=h))
    b.bind("<Leave>",lambda _,b=b,c=bg: b.configure(bg=c))
    return b

def _hline(parent,color=None,h=1):
    return tk.Frame(parent,bg=color or BORDER,height=h)

def _prog(parent):
    return ttk.Progressbar(parent,style="T.Horizontal.TProgressbar",mode="indeterminate")

def _combo(parent,var,values,width):
    return ttk.Combobox(parent,textvariable=var,values=values,width=width,state="readonly")

def _mktree(parent,cols,widths,stretch=None):
    f=tk.Frame(parent,bg=BG)
    f.rowconfigure(0,weight=1); f.columnconfigure(0,weight=1)
    tv=ttk.Treeview(f,columns=cols,show="headings",selectmode="extended",style="T.Treeview")
    for c in cols:
        tv.heading(c,text=c)
        tv.column(c,width=widths.get(c,100),minwidth=30,stretch=(c==stretch))
    vsb=ttk.Scrollbar(f,orient="vertical",style="T.Vertical.TScrollbar",command=tv.yview)
    hsb=ttk.Scrollbar(f,orient="horizontal",style="T.Horizontal.TScrollbar",command=tv.xview)
    tv.configure(yscrollcommand=vsb.set,xscrollcommand=hsb.set)
    tv.grid(row=0,column=0,sticky="nsew")
    vsb.grid(row=0,column=1,sticky="ns")
    hsb.grid(row=1,column=0,sticky="ew")
    return f,tv

def _popup(root,menu,event):
    try:    menu.tk_popup(event.x_root,event.y_root)
    finally: menu.grab_release()

def _set_icon(win):
    if os.path.exists(FAVICON):
        try: win.iconbitmap(FAVICON)
        except: pass

def _load_logo(target_width,bg_hex=SIDEBAR):
    if not os.path.exists(LOGO_FILE): return None
    if HAS_PIL:
        try:
            img=PILImage.open(LOGO_FILE).convert("RGBA")
            w,h=img.size
            new_h=max(1,int(h*(target_width/w)))
            img=img.resize((target_width,new_h),PILImage.LANCZOS)
            bg=PILImage.new("RGBA",img.size,bg_hex+"FF")
            bg.paste(img,mask=img.split()[3])
            return ImageTk.PhotoImage(bg.convert("RGB"))
        except: pass
    try:
        raw=tk.PhotoImage(file=LOGO_FILE)
        sub=max(1,raw.width()//target_width)
        return raw.subsample(sub,sub) if sub>1 else raw
    except: return None

# ─── API HELPERS ──────────────────────────────────────────────────────────────
def _clean(t): return re.sub(r"\s+"," ",str(t)).strip()

def _serper(query,api_key,gl,hl,num=10,page=1):
    payload={"q":query,"hl":hl,"num":num,"page":page}
    if gl: payload["gl"]=gl
    r=requests.post(SERPER_URL,
        headers={"X-API-KEY":api_key,"Content-Type":"application/json"},
        json=payload,timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def _extract_keywords(data,query,seen,out):
    def add(text,source):
        text=_clean(text)
        if not text or len(text)<3 or len(text)>200: return
        if text.lower().startswith(("http","www.")): return
        norm=text.rstrip("?!.,;:")
        if norm.lower() in _STOP: return
        key=norm.lower()
        if key in seen: return
        seen.add(key)
        words=norm.split()
        out.append({"keyword":norm,"source":source,"words":len(words),
                    "length":len(norm),"query_used":query,"score":len(words)*10+len(norm)})
    add(query,"Seed Keyword")
    for item in data.get("peopleAlsoAsk",[]): add(item.get("question",""),"People Also Ask")
    for item in data.get("relatedSearches",[]): add(item.get("query",""),"Related Search")
    for item in data.get("organic",[]):
        add(item.get("title",""),"Organic Title")
        for part in re.split(r"[.;!?\n]",item.get("snippet","")):
            if len(part.strip().split())>=3: add(part.strip(),"Organic Title")
        for sl in item.get("sitelinks",[]): add(sl.get("title",""),"Sitelink")
    ab=data.get("answerBox",{})
    for field in ("answer","snippet","title"):
        val=ab.get(field,"")
        if val:
            add(val,"Featured Snippet")
            for part in re.split(r"[.;!?\n]",val):
                if len(part.strip().split())>=3: add(part.strip(),"Featured Snippet")
    kg=data.get("knowledgeGraph",{})
    add(kg.get("title",""),"Knowledge Graph")
    add(kg.get("description",""),"Knowledge Graph")
    for v in kg.get("attributes",{}).values():
        if isinstance(v,str) and len(v.split())>=2: add(v,"Knowledge Graph")
    for item in data.get("topStories",[]): add(item.get("title",""),"Top Stories")

# ─── BODY TEXT EXTRACTOR (multi-strategy) ─────────────────────────────────────
def _extract_body_text(soup):
    for tag in soup(["script","style","nav","footer","header","aside",
                     "noscript","form","button","select","iframe",
                     "svg","meta","link"]):
        tag.decompose()
    for sel in ["article","main",'[role="main"]',"#content","#main",
                ".content",".post-content",".entry-content",".article-body"]:
        block=soup.select_one(sel)
        if block:
            t=re.sub(r"\s+"," ",block.get_text(separator=" ",strip=True)).strip()
            if len(t.split())>50: return t
    best=""; best_len=0
    for div in soup.find_all(["div","section","p"]):
        t=div.get_text(separator=" ",strip=True)
        if len(t)>best_len: best_len=len(t); best=t
    if best_len>200:
        return re.sub(r"\s+"," ",best).strip()
    return re.sub(r"\s+"," ",soup.get_text(separator=" ",strip=True)).strip()

def _tokenise(text):
    return [w for w in re.findall(r"\b[a-zA-Z]{2,}\b",text)
            if w.lower() not in DENSITY_STOP and len(w)>2]

def _calc_ngrams(tokens,n,top=30):
    lower=[t.lower() for t in tokens]
    if len(lower)<n: return []
    total=len(lower)
    ngrams=[" ".join(lower[i:i+n]) for i in range(len(lower)-n+1)]
    ctr=Counter(ngrams); out=[]
    for phrase,count in ctr.most_common(top):
        density=round((count/total)*100,2) if total else 0
        tag="ok" if 0.5<=density<=2.5 else ("warn" if density>2.5 else "low")
        out.append({"phrase":phrase,"n":n,"count":count,"density":density,"total":total,"tag":tag})
    return out

def _kw_density_in_text(text,keyword):
    if not keyword.strip(): return 0,0.0
    words=re.findall(r"\b\S+\b",text)
    total=len(words)
    if total==0: return 0,0.0
    pattern=r"\b"+re.escape(keyword.lower().strip())+r"\b"
    count=len(re.findall(pattern,text.lower()))
    return count,round((count/total)*100,2)

# ─── HELPER: safely collect @type from JSON-LD ────────────────────────────────
def _collect_type(schema_types, val):
    """FIX: @type can be a string OR a list — handle both without crashing dict.fromkeys()"""
    if isinstance(val, list):
        for item in val:
            if isinstance(item, str) and item:
                schema_types.append(item)
    elif isinstance(val, str) and val:
        schema_types.append(val)

# ─── FULL CRAWLER ─────────────────────────────────────────────────────────────
def _crawl(url):
    t0=time.time()
    sess=requests.Session()
    sess.headers.update({"User-Agent":UA,"Accept-Language":"en-US,en;q=0.9",
                         "Accept":"text/html,application/xhtml+xml"})
    resp=sess.get(url,timeout=TIMEOUT,allow_redirects=True)
    elapsed=round((time.time()-t0)*1000)
    try:    soup=BeautifulSoup(resp.text,"lxml")
    except: soup=BeautifulSoup(resp.text,"html.parser")
    parsed=urlparse(resp.url); base=f"{parsed.scheme}://{parsed.netloc}"
    def meta(name):
        tag=(soup.find("meta",attrs={"name":name}) or
             soup.find("meta",attrs={"property":name}))
        return (tag.get("content","") or "").strip() if tag else ""
    def og(prop):
        tag=soup.find("meta",property=f"og:{prop}")
        return (tag.get("content","") or "").strip() if tag else ""
    def tw(prop):
        tag=soup.find("meta",attrs={"name":f"twitter:{prop}"})
        return (tag.get("content","") or "").strip() if tag else ""
    title=(soup.title.string or "").strip() if soup.title else ""
    desc=meta("description")
    can_tag=soup.find("link",rel="canonical")
    canonical=can_tag.get("href","").strip() if can_tag else ""
    get_tags=lambda tag:[el.get_text(strip=True) for el in soup.find_all(tag)]
    body_text=_extract_body_text(BeautifulSoup(resp.text,"lxml"))
    word_count=len(body_text.split())
    sentences=[s.strip() for s in re.split(r"[.!?]+",body_text) if len(s.strip().split())>3]
    avg_sw=round(sum(len(s.split()) for s in sentences)/len(sentences),1) if sentences else 0
    imgs=soup.find_all("img")
    imgs_no_alt=[im.get("src","") or im.get("data-src","") for im in imgs
                 if not im.get("alt","").strip()]
    internal_links,external_links,nofollow_count=[],[],0
    for a in soup.find_all("a",href=True):
        href=a["href"].strip()
        if not href or href.startswith(("#","mailto:","tel:","javascript:")): continue
        full=urljoin(base,href); txt=a.get_text(strip=True)[:80]
        # FIX: rel is a list in BS4 for multi-valued attrs
        rel=a.get("rel",[])
        if isinstance(rel,str): rel=[rel]
        if any(r=="nofollow" for r in rel): nofollow_count+=1
        entry={"text":txt,"url":full}
        if urlparse(full).netloc==parsed.netloc: internal_links.append(entry)
        else: external_links.append(entry)

    # ── FIX: schema_types - handle @type being a list ──────────────────────────
    schema_types=[]
    for tag in soup.find_all("script",type="application/ld+json"):
        try:
            d=json.loads(tag.string or "")
            if isinstance(d,list):
                for item in d:
                    if isinstance(item,dict):
                        _collect_type(schema_types, item.get("@type",""))
            elif isinstance(d,dict):
                _collect_type(schema_types, d.get("@type",""))
                for node in d.get("@graph",[]):
                    if isinstance(node,dict):
                        _collect_type(schema_types, node.get("@type",""))
        except:
            # fallback regex — only extracts strings, no list issue
            found=re.findall(r'"@type"\s*:\s*"([^"]+)"',tag.string or "")
            schema_types.extend(found)
    # Deduplicate preserving order (all items are now guaranteed strings)
    seen_st=set(); deduped=[]
    for st in schema_types:
        if st not in seen_st:
            seen_st.add(st); deduped.append(st)
    schema_types=deduped

    # ── FIX: hreflang — rel is multi-value list in BS4 ────────────────────────
    hreflang=[]
    for t in soup.find_all("link"):
        rel_val=t.get("rel",[])
        if isinstance(rel_val,str): rel_val=[rel_val]
        if "alternate" in rel_val and t.get("hreflang"):
            hreflang.append(t.get("hreflang",""))

    page_size_kb=round(len(resp.content)/1024,1)
    cs_tag=soup.find("meta",charset=True)
    return {
        "url":resp.url,"status_code":resp.status_code,"load_ms":elapsed,
        "page_size_kb":page_size_kb,"https_ok":resp.url.startswith("https://"),
        "has_mixed":bool(re.search(r'src=["\']http://',resp.text)),
        "redirected":(resp.url!=url),
        "title":title,"title_len":len(title),"description":desc,"desc_len":len(desc),
        "canonical":canonical,"robots_meta":meta("robots"),"keywords_meta":meta("keywords"),
        "viewport":meta("viewport"),"charset":(cs_tag.get("charset","") if cs_tag else ""),
        "hreflang":hreflang,
        "h1":get_tags("h1"),"h2":get_tags("h2"),"h3":get_tags("h3"),
        "word_count":word_count,"avg_sentence_words":avg_sw,
        "img_total":len(imgs),"img_no_alt":len(imgs_no_alt),"img_no_alt_list":imgs_no_alt[:20],
        "internal_links":internal_links,"external_links":external_links,
        "nofollow_count":nofollow_count,"schema_types":schema_types,
        "has_faq":"FAQPage" in schema_types,
        "has_breadcrumb":"BreadcrumbList" in schema_types,
        "has_article":any(t in schema_types for t in ["Article","BlogPosting","NewsArticle"]),
        "sitemap_url":f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
        "server":resp.headers.get("server",""),
        "cache_control":resp.headers.get("cache-control",""),
        "x_powered_by":resp.headers.get("x-powered-by",""),
        "social":{"og:title":og("title"),"og:description":og("description"),
                  "og:image":og("image"),"og:url":og("url"),
                  "twitter:card":tw("card"),"twitter:title":tw("title")},
    }

# ─── PAGESPEED ────────────────────────────────────────────────────────────────
def _sc(s):
    if s is None: return FG3
    v=float(s)*100
    return SUCCESS if v>=90 else (WARNING if v>=50 else DANGER)

def _fetch_ps(url,api_key,strategy):
    r=requests.get(PS_URL,params={"url":url,"key":api_key,"strategy":strategy},timeout=TIMEOUT)
    r.raise_for_status(); return r.json()

def _fmt_score(s): return str(round(s*100)) if s is not None else "--"

def _parse_ps(data,strategy):
    cats=data.get("lighthouseResult",{}).get("categories",{})
    audits=data.get("lighthouseResult",{}).get("audits",{})
    ga=lambda k:audits.get(k,{})
    perf=cats.get("performance",{}).get("score"); acc=cats.get("accessibility",{}).get("score")
    seo=cats.get("seo",{}).get("score"); bp=cats.get("best-practices",{}).get("score")
    cats_out=[("Performance",_fmt_score(perf),_sc(perf))]
    if acc is not None: cats_out.append(("Accessibility",_fmt_score(acc),_sc(acc)))
    if bp  is not None: cats_out.append(("Best Practices",_fmt_score(bp),_sc(bp)))
    if seo is not None: cats_out.append(("SEO",_fmt_score(seo),_sc(seo)))
    opps=[]
    for k,audit in audits.items():
        sc=audit.get("score")
        if sc is not None and float(sc)<0.9:
            t=audit.get("title",""); d=audit.get("displayValue","")
            if t and d: opps.append((t[:60],d[:28]))
    return {
        "strategy":strategy.upper(),"performance":round((perf or 0)*100),
        "perf_color":_sc(perf),"categories":cats_out,
        "metrics":[
            ("FCP",   ga("first-contentful-paint").get("displayValue","N/A"),   ga("first-contentful-paint").get("score")),
            ("LCP",   ga("largest-contentful-paint").get("displayValue","N/A"), ga("largest-contentful-paint").get("score")),
            ("TBT",   ga("total-blocking-time").get("displayValue","N/A"),      ga("total-blocking-time").get("score")),
            ("CLS",   ga("cumulative-layout-shift").get("displayValue","N/A"),  ga("cumulative-layout-shift").get("score")),
            ("SI",    ga("speed-index").get("displayValue","N/A"),              ga("speed-index").get("score")),
            ("TTI",   ga("interactive").get("displayValue","N/A"),              ga("interactive").get("score")),
        ],
        "opportunities":opps[:6],
    }

# ─── SCHEMA DATA ──────────────────────────────────────────────────────────────
SCHEMA_TYPES = [
    "Article","NewsArticle","BlogPosting","WebPage","WebSite","Product",
    "LocalBusiness","Restaurant","Organization","Person","FAQPage",
    "BreadcrumbList","Event","VideoObject","Recipe","HowTo",
    "SoftwareApplication","JobPosting","Review",
]
SCHEMA_FIELDS = {
    "Article":[
        ("url","Page URL","https://example.com/article",False,True),
        ("headline","Headline","Article title (max 110 chars)",False,True),
        ("description","Description","Short description",True,False),
        ("image","Image URL","https://example.com/image.jpg",False,False),
        ("author_name","Author Name","John Doe",False,False),
        ("author_url","Author URL","https://example.com/author",False,False),
        ("publisher","Publisher Name","Example Media",False,False),
        ("logo_url","Publisher Logo URL","https://example.com/logo.png",False,False),
        ("date_published","Date Published",TODAY,False,False),
        ("date_modified","Date Modified",TODAY,False,False),
        ("article_body","Article Body","Full article text",True,False),
    ],
    "NewsArticle":[
        ("url","Page URL","https://example.com/news",False,True),
        ("headline","Headline","News headline",False,True),
        ("description","Description","Short summary",True,False),
        ("image","Image URL","https://example.com/image.jpg",False,False),
        ("author_name","Author Name","Jane Smith",False,False),
        ("publisher","Publisher Name","Daily News",False,False),
        ("logo_url","Publisher Logo URL","https://example.com/logo.png",False,False),
        ("date_published","Date Published",TODAY,False,False),
        ("date_modified","Date Modified",TODAY,False,False),
    ],
    "BlogPosting":[
        ("url","Page URL","https://example.com/blog/post",False,True),
        ("headline","Post Title","Blog post title",False,True),
        ("description","Excerpt","Brief excerpt",True,False),
        ("image","Featured Image URL","https://example.com/image.jpg",False,False),
        ("author_name","Author Name","Author",False,False),
        ("author_url","Author Profile URL","https://example.com/author",False,False),
        ("publisher","Blog / Site Name","My Blog",False,False),
        ("logo_url","Site Logo URL","https://example.com/logo.png",False,False),
        ("date_published","Date Published",TODAY,False,False),
        ("date_modified","Date Modified",TODAY,False,False),
        ("keywords","Keywords (comma sep.)","seo, blogging, tips",False,False),
    ],
    "WebPage":[
        ("url","Page URL","https://example.com/page",False,True),
        ("name","Page Name","About Us",False,True),
        ("description","Description","What this page is about",True,False),
        ("image","Image URL","https://example.com/image.jpg",False,False),
        ("publisher","Site / Publisher Name","Example Site",False,False),
        ("date_published","Date Published",TODAY,False,False),
        ("date_modified","Date Modified",TODAY,False,False),
    ],
    "WebSite":[
        ("url","Site URL","https://example.com/",False,True),
        ("name","Site Name","Example Site",False,True),
        ("description","Site Description","What your site is about",True,False),
        ("search_url","Search URL Template","https://example.com/?s={search_term_string}",False,False),
        ("publisher","Publisher / Owner","Owner Name",False,False),
    ],
    "Product":[
        ("url","Product URL","https://example.com/product",False,True),
        ("name","Product Name","Product name",False,True),
        ("description","Description","Describe the product",True,False),
        ("image","Product Image URL","https://example.com/product.jpg",False,False),
        ("brand","Brand","Brand Name",False,False),
        ("sku","SKU","SKU-12345",False,False),
        ("price","Price","29.99",False,False),
        ("currency","Currency","USD",False,False),
        ("availability","Availability","InStock",False,False),
        ("rating_value","Rating Value","4.5",False,False),
        ("rating_count","Rating Count","128",False,False),
    ],
    "LocalBusiness":[
        ("url","Website URL","https://example.com/",False,True),
        ("name","Business Name","My Local Business",False,True),
        ("description","Description","What your business does",True,False),
        ("image","Business Image URL","https://example.com/image.jpg",False,False),
        ("telephone","Phone Number","+1-800-555-1234",False,False),
        ("email","Email","contact@business.com",False,False),
        ("street","Street Address","123 Main St",False,False),
        ("city","City","Springfield",False,False),
        ("region","State / Region","IL",False,False),
        ("postal","Postal Code","62701",False,False),
        ("country","Country","US",False,False),
        ("hours","Opening Hours","Mo-Fr 09:00-18:00",False,False),
        ("price_range","Price Range","$$",False,False),
        ("rating_value","Rating Value","4.5",False,False),
        ("rating_count","Rating Count","80",False,False),
    ],
    "Restaurant":[
        ("url","Website URL","https://example.com/",False,True),
        ("name","Restaurant Name","The Great Eatery",False,True),
        ("description","Description","Italian fine dining",True,False),
        ("cuisine","Cuisine Type","Italian, Mediterranean",False,False),
        ("telephone","Phone Number","+1-800-555-1234",False,False),
        ("street","Street Address","123 Main St",False,False),
        ("city","City","New York",False,False),
        ("region","State / Region","NY",False,False),
        ("postal","Postal Code","10001",False,False),
        ("country","Country","US",False,False),
        ("hours","Opening Hours","Mo-Su 11:00-23:00",False,False),
        ("price_range","Price Range","$$",False,False),
        ("rating_value","Rating","4.7",False,False),
        ("rating_count","Review Count","210",False,False),
    ],
    "Organization":[
        ("url","Website URL","https://example.com/",False,True),
        ("name","Organization Name","ACME Corp",False,True),
        ("description","Description","What the org does",True,False),
        ("logo","Logo URL","https://example.com/logo.png",False,False),
        ("telephone","Phone","+1-800-555-0000",False,False),
        ("email","Email","info@acme.com",False,False),
        ("street","Street Address","1 Corporate Plaza",False,False),
        ("city","City","New York",False,False),
        ("region","State / Region","NY",False,False),
        ("postal","Postal Code","10001",False,False),
        ("country","Country","US",False,False),
        ("founding_year","Founding Year","2010",False,False),
        ("social_1","Social URL 1","https://twitter.com/acme",False,False),
        ("social_2","Social URL 2","https://linkedin.com/company/acme",False,False),
    ],
    "Person":[
        ("url","Profile URL","https://example.com/person",False,True),
        ("name","Full Name","Jane Doe",False,True),
        ("job_title","Job Title","Software Engineer",False,False),
        ("description","Bio","Short biography",True,False),
        ("image","Photo URL","https://example.com/photo.jpg",False,False),
        ("email","Email","jane@example.com",False,False),
        ("employer","Employer / Company","ACME Corp",False,False),
        ("employer_url","Employer URL","https://acme.com",False,False),
        ("social_1","Social URL 1","https://twitter.com/janedoe",False,False),
        ("social_2","Social URL 2","https://linkedin.com/in/janedoe",False,False),
    ],
    "FAQPage":[
        ("url","Page URL","https://example.com/faq",False,True),
        ("q1","Question 1","What is...?",False,True),
        ("a1","Answer 1","Answer to question 1",True,True),
        ("q2","Question 2","How do I...?",False,False),
        ("a2","Answer 2","Answer to question 2",True,False),
        ("q3","Question 3","Why does...?",False,False),
        ("a3","Answer 3","Answer to question 3",True,False),
        ("q4","Question 4","When should...?",False,False),
        ("a4","Answer 4","Answer to question 4",True,False),
        ("q5","Question 5","Can I...?",False,False),
        ("a5","Answer 5","Answer to question 5",True,False),
    ],
    "BreadcrumbList":[
        ("item1_name","Item 1 Name","Home",False,True),
        ("item1_url","Item 1 URL","https://example.com/",False,True),
        ("item2_name","Item 2 Name","Category",False,False),
        ("item2_url","Item 2 URL","https://example.com/category/",False,False),
        ("item3_name","Item 3 Name","Sub-Category",False,False),
        ("item3_url","Item 3 URL","https://example.com/category/sub/",False,False),
        ("item4_name","Item 4 Name","Page Title",False,False),
        ("item4_url","Item 4 URL","https://example.com/category/sub/page/",False,False),
    ],
    "Event":[
        ("url","Event URL","https://example.com/event",False,True),
        ("name","Event Name","Annual Conference 2026",False,True),
        ("description","Description","What the event is about",True,False),
        ("image","Event Image URL","https://example.com/event.jpg",False,False),
        ("start","Start Date and Time",f"{TODAY}T09:00:00",False,True),
        ("end","End Date and Time",f"{TODAY}T17:00:00",False,False),
        ("location_name","Venue Name","Convention Center",False,False),
        ("street","Street Address","100 Event Blvd",False,False),
        ("city","City","Los Angeles",False,False),
        ("region","State / Region","CA",False,False),
        ("postal","Postal Code","90001",False,False),
        ("country","Country","US",False,False),
        ("organizer","Organizer Name","ACME Events",False,False),
        ("price","Ticket Price","25.00",False,False),
        ("currency","Currency","USD",False,False),
    ],
    "VideoObject":[
        ("url","Page URL","https://example.com/video",False,True),
        ("name","Video Title","How to bake sourdough bread",False,True),
        ("description","Description","In this video we show...",True,False),
        ("thumbnail","Thumbnail URL","https://example.com/thumb.jpg",False,False),
        ("upload_date","Upload Date",TODAY,False,False),
        ("duration","Duration (ISO 8601)","PT5M30S",False,False),
        ("embed_url","Embed URL","https://www.youtube.com/embed/xxx",False,False),
        ("publisher","Publisher","My Channel",False,False),
    ],
    "Recipe":[
        ("url","Recipe URL","https://example.com/recipe",False,True),
        ("name","Recipe Name","Classic Banana Bread",False,True),
        ("description","Description","A simple moist banana bread",True,False),
        ("image","Image URL","https://example.com/recipe.jpg",False,False),
        ("author_name","Author Name","Chef Julia",False,False),
        ("prep_time","Prep Time (ISO 8601)","PT15M",False,False),
        ("cook_time","Cook Time (ISO 8601)","PT1H",False,False),
        ("total_time","Total Time (ISO 8601)","PT1H15M",False,False),
        ("servings","Recipe Yield","8 slices",False,False),
        ("calories","Calories","280 calories",False,False),
        ("ingredients","Ingredients (one per line)","3 ripe bananas\n2 cups flour",True,False),
        ("keywords","Keywords","banana bread, easy, moist",False,False),
        ("rating_value","Rating","4.8",False,False),
        ("rating_count","Review Count","156",False,False),
    ],
    "HowTo":[
        ("url","Page URL","https://example.com/how-to",False,True),
        ("name","How To Title","How to change a tire",False,True),
        ("description","Description","Step-by-step guide",True,False),
        ("image","Image URL","https://example.com/image.jpg",False,False),
        ("total_time","Total Time (ISO 8601)","PT30M",False,False),
        ("step1","Step 1 Name","Gather tools",False,True),
        ("step1_text","Step 1 Instructions","Collect a jack, lug wrench...",True,True),
        ("step2","Step 2 Name","Loosen lug nuts",False,False),
        ("step2_text","Step 2 Instructions","Use the wrench to loosen...",True,False),
        ("step3","Step 3 Name","Raise the vehicle",False,False),
        ("step3_text","Step 3 Instructions","Place the jack under...",True,False),
        ("step4","Step 4 Name","Remove the flat tire",False,False),
        ("step4_text","Step 4 Instructions","Pull the flat tire straight out...",True,False),
        ("step5","Step 5 Name","Mount the spare",False,False),
        ("step5_text","Step 5 Instructions","Align the spare tire...",True,False),
    ],
    "SoftwareApplication":[
        ("url","App URL","https://example.com/app",False,True),
        ("name","App Name","My Awesome App",False,True),
        ("description","Description","What the app does",True,False),
        ("os","Operating System","Windows, macOS, Android, iOS",False,False),
        ("category","App Category","BusinessApplication",False,False),
        ("price","Price","0 (Free) or 4.99",False,False),
        ("currency","Currency","USD",False,False),
        ("rating_value","Rating","4.5",False,False),
        ("rating_count","Rating Count","500",False,False),
        ("developer","Developer / Author","ACME Dev",False,False),
        ("version","Software Version","2.1.0",False,False),
    ],
    "JobPosting":[
        ("url","Job Posting URL","https://example.com/jobs/role",False,True),
        ("title","Job Title","SEO Manager",False,True),
        ("description","Full Job Description","We are looking for...",True,True),
        ("employer","Employer Name","ACME Corp",False,True),
        ("date_posted","Date Posted",TODAY,False,False),
        ("valid_through","Valid Through","2026-06-30T00:00:00",False,False),
        ("employment_type","Employment Type","FULL_TIME",False,False),
        ("location","Job Location","New York, NY",False,False),
        ("remote","Remote OK?","true / false",False,False),
        ("salary_min","Salary Min","50000",False,False),
        ("salary_max","Salary Max","70000",False,False),
        ("salary_unit","Salary Unit","YEAR / MONTH / HOUR",False,False),
        ("currency","Currency","USD",False,False),
    ],
    "Review":[
        ("url","Review URL","https://example.com/review",False,True),
        ("item_name","Item Being Reviewed","MacBook Pro 16",False,True),
        ("item_type","Item Type (@type)","Product / Book / Movie / LocalBusiness",False,False),
        ("review_body","Review Text","Full review content...",True,True),
        ("author_name","Reviewer Name","Jane Doe",False,True),
        ("rating_value","Rating (1-5)","4.5",False,False),
        ("rating_best","Best Possible Rating","5",False,False),
        ("date_published","Date Published",TODAY,False,False),
        ("publisher","Publisher","Tech Reviews Daily",False,False),
    ],
}

def _sv(vals,key): return vals.get(key,"").strip()

def _addr(vals):
    s=_sv(vals,"street"); ci=_sv(vals,"city"); r=_sv(vals,"region")
    po=_sv(vals,"postal"); co=_sv(vals,"country")
    if not any([s,ci,r,po,co]): return None
    a={"@type":"PostalAddress"}
    if s:  a["streetAddress"]=s
    if ci: a["addressLocality"]=ci
    if r:  a["addressRegion"]=r
    if po: a["postalCode"]=po
    if co: a["addressCountry"]=co
    return a

def _agg_rating(vals):
    rv=_sv(vals,"rating_value"); rc=_sv(vals,"rating_count"); best=_sv(vals,"rating_best") or "5"
    if not rv: return None
    r={"@type":"AggregateRating","ratingValue":rv,"bestRating":best}
    if rc: r["ratingCount"]=rc
    return r

def _offer(vals):
    p=_sv(vals,"price"); c=_sv(vals,"currency") or "USD"; av=_sv(vals,"availability")
    if not p: return None
    o={"@type":"Offer","price":p,"priceCurrency":c}
    if av:
        m={"InStock":"https://schema.org/InStock","OutOfStock":"https://schema.org/OutOfStock",
           "PreOrder":"https://schema.org/PreOrder"}
        o["availability"]=m.get(av,f"https://schema.org/{av}")
    return o

def build_jsonld(schema_type,vals):
    v=lambda k:_sv(vals,k)
    ld={"@context":"https://schema.org","@type":schema_type}
    if schema_type in ("Article","NewsArticle","BlogPosting"):
        if v("url"):            ld["mainEntityOfPage"]={"@type":"WebPage","@id":v("url")}
        if v("headline"):       ld["headline"]=v("headline")
        if v("description"):    ld["description"]=v("description")
        if v("image"):          ld["image"]=v("image")
        if v("date_published"): ld["datePublished"]=v("date_published")
        if v("date_modified"):  ld["dateModified"]=v("date_modified")
        if v("author_name"):
            a={"@type":"Person","name":v("author_name")}
            if v("author_url"): a["url"]=v("author_url")
            ld["author"]=a
        if v("publisher"):
            p={"@type":"Organization","name":v("publisher")}
            if v("logo_url"): p["logo"]={"@type":"ImageObject","url":v("logo_url")}
            ld["publisher"]=p
        if v("keywords"):     ld["keywords"]=v("keywords")
        if v("article_body"): ld["articleBody"]=v("article_body")
    elif schema_type=="WebPage":
        for k,sk in [("url","url"),("name","name"),("description","description"),
                     ("image","image"),("date_published","datePublished"),("date_modified","dateModified")]:
            if v(k): ld[sk]=v(k)
        if v("publisher"): ld["publisher"]={"@type":"Organization","name":v("publisher")}
    elif schema_type=="WebSite":
        for k,sk in [("url","url"),("name","name"),("description","description")]:
            if v(k): ld[sk]=v(k)
        if v("publisher"): ld["publisher"]={"@type":"Organization","name":v("publisher")}
        if v("search_url"):
            ld["potentialAction"]={"@type":"SearchAction",
                "target":{"@type":"EntryPoint","urlTemplate":v("search_url")},
                "query-input":"required name=search_term_string"}
    elif schema_type=="Product":
        for k,sk in [("url","url"),("name","name"),("description","description"),("image","image"),("sku","sku")]:
            if v(k): ld[sk]=v(k)
        if v("brand"): ld["brand"]={"@type":"Brand","name":v("brand")}
        o=_offer(vals)
        if o: ld["offers"]=o
        r=_agg_rating(vals)
        if r: ld["aggregateRating"]=r
    elif schema_type in ("LocalBusiness","Restaurant"):
        if schema_type=="Restaurant" and v("cuisine"): ld["servesCuisine"]=v("cuisine")
        for k,sk in [("url","url"),("name","name"),("description","description"),("image","image"),
                     ("telephone","telephone"),("email","email"),("hours","openingHours"),("price_range","priceRange")]:
            if v(k): ld[sk]=v(k)
        a=_addr(vals)
        if a: ld["address"]=a
        r=_agg_rating(vals)
        if r: ld["aggregateRating"]=r
    elif schema_type=="Organization":
        for k,sk in [("url","url"),("name","name"),("description","description"),("logo","logo"),
                     ("telephone","telephone"),("email","email")]:
            if v(k): ld[sk]=v(k)
        a=_addr(vals)
        if a: ld["address"]=a
        if v("founding_year"): ld["foundingDate"]=v("founding_year")
        sa=[v(k) for k in ("social_1","social_2") if v(k)]
        if sa: ld["sameAs"]=sa
    elif schema_type=="Person":
        for k,sk in [("url","url"),("name","name"),("job_title","jobTitle"),("description","description"),
                     ("image","image"),("email","email")]:
            if v(k): ld[sk]=v(k)
        if v("employer"):
            w={"@type":"Organization","name":v("employer")}
            if v("employer_url"): w["url"]=v("employer_url")
            ld["worksFor"]=w
        sa=[v(k) for k in ("social_1","social_2") if v(k)]
        if sa: ld["sameAs"]=sa
    elif schema_type=="FAQPage":
        if v("url"): ld["url"]=v("url")
        ents=[]
        for i in range(1,6):
            q=v(f"q{i}"); a=v(f"a{i}")
            if q and a: ents.append({"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}})
        if ents: ld["mainEntity"]=ents
    elif schema_type=="BreadcrumbList":
        items=[]
        for i in range(1,5):
            n=v(f"item{i}_name"); u=v(f"item{i}_url")
            if n and u: items.append({"@type":"ListItem","position":len(items)+1,"name":n,"item":u})
        if items: ld["itemListElement"]=items
    elif schema_type=="Event":
        for k,sk in [("url","url"),("name","name"),("description","description"),
                     ("image","image"),("start","startDate"),("end","endDate")]:
            if v(k): ld[sk]=v(k)
        loc={}
        if v("location_name"): loc["name"]=v("location_name")
        a=_addr(vals)
        if a: loc["address"]=a
        if loc: loc["@type"]="Place"; ld["location"]=loc
        if v("price"):
            ld["offers"]={"@type":"Offer","price":v("price"),
                          "priceCurrency":v("currency") or "USD","url":v("url")}
    elif schema_type=="VideoObject":
        for k,sk in [("url","url"),("name","name"),("description","description"),
                     ("thumbnail","thumbnailUrl"),("upload_date","uploadDate"),("embed_url","embedUrl")]:
            if v(k): ld[sk]=v(k)
        if v("duration"): ld["duration"]=v("duration").split()[0]
        if v("publisher"): ld["publisher"]={"@type":"Organization","name":v("publisher")}
    elif schema_type=="Recipe":
        for k,sk in [("url","url"),("name","name"),("description","description"),("image","image"),
                     ("prep_time","prepTime"),("cook_time","cookTime"),("total_time","totalTime"),
                     ("servings","recipeYield"),("keywords","keywords")]:
            if v(k): ld[sk]=v(k)
        if v("author_name"): ld["author"]={"@type":"Person","name":v("author_name")}
        if v("calories"):    ld["nutrition"]={"@type":"NutritionInformation","calories":v("calories")}
        if v("ingredients"):
            lines=[l.strip() for l in v("ingredients").split("\n") if l.strip()]
            if lines: ld["recipeIngredient"]=lines
        r=_agg_rating(vals)
        if r: ld["aggregateRating"]=r
    elif schema_type=="HowTo":
        for k,sk in [("url","url"),("name","name"),("description","description"),
                     ("image","image"),("total_time","totalTime")]:
            if v(k): ld[sk]=v(k)
        steps=[]
        for i in range(1,6):
            sn=v(f"step{i}"); st=v(f"step{i}_text")
            if sn and st: steps.append({"@type":"HowToStep","name":sn,"text":st})
        if steps: ld["step"]=steps
    elif schema_type=="SoftwareApplication":
        for k,sk in [("url","url"),("name","name"),("description","description"),
                     ("os","operatingSystem"),("category","applicationCategory"),("version","softwareVersion")]:
            if v(k): ld[sk]=v(k)
        if v("developer"): ld["author"]={"@type":"Person","name":v("developer")}
        o=_offer(vals)
        if o: ld["offers"]=o
        r=_agg_rating(vals)
        if r: ld["aggregateRating"]=r
    elif schema_type=="JobPosting":
        for k,sk in [("url","url"),("title","title"),("description","description"),
                     ("date_posted","datePosted"),("valid_through","validThrough"),
                     ("employment_type","employmentType")]:
            if v(k): ld[sk]=v(k)
        if v("location"):
            ld["jobLocation"]={"@type":"Place","address":{"@type":"PostalAddress","addressLocality":v("location")}}
        if v("remote").lower() in ("true","yes","1"): ld["jobLocationType"]="TELECOMMUTE"
        if v("employer"):
            org={"@type":"Organization","name":v("employer")}
            if v("employer_url"): org["sameAs"]=v("employer_url")
            ld["hiringOrganization"]=org
        if v("salary_min") or v("salary_max"):
            sal={"@type":"MonetaryAmount","currency":v("currency") or "USD",
                 "value":{"@type":"QuantitativeValue"}}
            if v("salary_min"): sal["value"]["minValue"]=v("salary_min")
            if v("salary_max"): sal["value"]["maxValue"]=v("salary_max")
            if v("salary_unit"):sal["value"]["unitText"]=v("salary_unit")
            ld["baseSalary"]=sal
    elif schema_type=="Review":
        if v("url"):  ld["url"]=v("url")
        if v("item_name"):
            ld["itemReviewed"]={"@type":v("item_type") or "Product","name":v("item_name")}
        if v("review_body"):    ld["reviewBody"]=v("review_body")
        if v("date_published"): ld["datePublished"]=v("date_published")
        if v("author_name"):
            a={"@type":"Person","name":v("author_name")}
            if v("author_url"): a["url"]=v("author_url")
            ld["author"]=a
        if v("publisher"): ld["publisher"]={"@type":"Organization","name":v("publisher")}
        if v("rating_value"):
            ld["reviewRating"]={"@type":"Rating","ratingValue":v("rating_value"),
                                 "bestRating":v("rating_best") or "5"}
    return ld

# ═══════════════════════════════════════════════════════════════════════════════
# SPLASH  (MGS2-style codec animation — FIXED panel sizing & animation math)
# ═══════════════════════════════════════════════════════════════════════════════
class Splash(tk.Toplevel):
    BOOT = [
        ("SOLITON KIT  " + VERSION + "  ONLINE",        "ac"),
        ("",                                              "dm"),
        ("SYS  Python runtime ................. OK",     "ok"),
        ("SYS  tkinter GUI .................... OK",     "ok"),
        ("SYS  requests ........................ OK",    "ok"),
        ("SYS  beautifulsoup4 .................. OK",    "ok"),
        ("SYS  lxml parser ..................... OK",    "ok"),
        ("",                                              "dm"),
        ("CFG  Loading config .................",         "f2"),
        ("CFG  Configuration loaded",                    "ok"),
        ("",                                              "dm"),
        ("MOD  Keyword Extractor .............. READY",  "ok"),
        ("MOD  On-Page SEO Crawler ............ READY",  "ok"),
        ("MOD  PageSpeed Monitor .............. READY",  "ok"),
        ("MOD  Keyword Density ................ READY",  "ok"),
        ("MOD  Schema Generator ............... READY",  "ok"),
        ("",                                              "dm"),
        ("ALL SYSTEMS NOMINAL  LAUNCHING",                "ac"),
    ]
    COLORS = {"ac":ACCENT,"ok":SUCCESS,"wn":WARNING,"dm":FG3,"f2":FG2}

    def __init__(self, master, on_done):
        super().__init__(master)
        self._on_done = on_done
        self._done    = False
        # ── FIX: use a fixed reasonable size that fits all screens ──
        W, H = 860, 520
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        # Clamp to screen if necessary
        W = min(W, sw - 40)
        H = min(H, sh - 80)
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.overrideredirect(True)
        self.configure(bg="#000000")
        self.attributes("-topmost", True)
        try: self.attributes("-alpha", 0.97)
        except: pass

        self.W, self.H = W, H
        self._phase   = 0
        self._tick    = 0
        self._slide   = 0.0
        self._typed   = 0
        self._line    = 0
        self._char    = 0
        self._log_lines = []
        self._prog_val  = 0.0

        # ── FIX: panel width so both fit side-by-side with a gap ──
        GAP = 8
        self._pw = (W - GAP) // 2    # each panel width
        self._ph = int(H * 0.82)
        self._py = (H - self._ph) // 2

        self.cv = tk.Canvas(self, bg="#000000", highlightthickness=0, width=W, height=H)
        self.cv.pack(fill="both", expand=True)

        self.bind("<Key>",    lambda _: self._finish())
        self.bind("<Button>", lambda _: self._finish())
        self._run()

    # ── panel final positions ──────────────────────────────────────────────────
    def _final_lx(self): return 0
    def _final_rx(self): return self._pw + 8

    # ── animation helpers ─────────────────────────────────────────────────────
    def _run(self):
        if self._done: return
        if   self._phase == 0: self._phase_static()
        elif self._phase == 1: self._phase_slide()
        elif self._phase == 2: self._phase_header()
        elif self._phase == 3: self._phase_boot()
        elif self._phase == 4: self._phase_finish_anim()

    def _schedule(self, delay=20):
        if self._done: return
        self.after(delay, self._run)

    # ── phase 0: static noise ─────────────────────────────────────────────────
    def _phase_static(self):
        import random
        cv = self.cv; cv.delete("all")
        for y in range(0, self.H, 3):
            a = random.randint(0, 35)
            cv.create_line(0, y, self.W, y, fill=f"#{a:02x}{a+5:02x}{a+15:02x}")
        if self._tick % 3 == 0:
            cv.create_text(self.W//2, self.H//2, text="CONNECTING...",
                           font=("Consolas",14,"bold"), fill=ACCENT, anchor="center")
        self._tick += 1
        if self._tick >= 15: self._phase = 1; self._slide = 0.0
        self._schedule(40)

    # ── phase 1: panels slide in ──────────────────────────────────────────────
    def _phase_slide(self):
        self._slide = min(1.0, self._slide + 0.09)
        self._draw_frame()
        if self._slide >= 1.0: self._phase = 2; self._typed = 0
        self._schedule(16)

    # ── phase 2: header types ─────────────────────────────────────────────────
    _HDR = "[ SOLITON KIT  " + VERSION + " ]"

    def _phase_header(self):
        self._typed = min(len(self._HDR), self._typed + 2)
        self._draw_frame()
        if self._typed >= len(self._HDR): self._phase = 3; self._line = 0; self._char = 0
        self._schedule(22)

    # ── phase 3: boot log types ───────────────────────────────────────────────
    def _phase_boot(self):
        if self._line >= len(self.BOOT):
            self._phase = 4; self._prog_val = 0.0; self._schedule(); return
        text, col_key = self.BOOT[self._line]
        if not text:
            self._log_lines.append(("", "dm"))
            self._line += 1; self._char = 0; self._schedule(6); return
        self._char = min(len(text), self._char + 3)
        if self._char >= len(text):
            self._log_lines.append((text, col_key))
            self._draw_frame()
            self._line += 1; self._char = 0
            self._schedule(55 if text.startswith("ALL") else 14)
        else:
            self._draw_frame(partial=(text[:self._char], col_key))
            self._schedule(8)

    # ── phase 4: progress bar → launch ────────────────────────────────────────
    def _phase_finish_anim(self):
        self._prog_val = min(1.0, self._prog_val + 0.045)
        self._draw_frame()
        if self._prog_val >= 1.0: self._finish()
        else: self._schedule(18)

    # ── master draw ───────────────────────────────────────────────────────────
    def _draw_frame(self, partial=None):
        cv = self.cv; cv.delete("all")
        W, H, pw, ph, py = self.W, self.H, self._pw, self._ph, self._py

        # background
        cv.create_rectangle(0, 0, W, H, fill="#000305", outline="")
        for y in range(0, H, 4):
            cv.create_line(0, y, W, y, fill="#030D18")

        if self._phase == 0: return

        # ── FIX: clean slide-in math ──────────────────────────────────────────
        # Left panel: slides from x=-pw to x=0
        lx = int(-pw + pw * self._slide)
        # Right panel: slides from x=W to x=pw+8
        rx_final = self._final_rx()
        rx = int(W - (W - rx_final) * self._slide)

        self._draw_panel(cv, lx, py, pw, ph, left=True)
        self._draw_panel(cv, rx, py, pw, ph, left=False)

        # gap stripe between panels
        if self._slide > 0.5:
            gap_x = lx + pw
            cv.create_rectangle(gap_x, py, gap_x + 8, py + ph, fill="#000810", outline="")
            cv.create_line(gap_x,     py, gap_x,     py+ph, fill=BORDER2)
            cv.create_line(gap_x + 7, py, gap_x + 7, py+ph, fill=BORDER2)

        # ── header text — centered in left panel only ─────────────────────────
        if self._phase >= 2:
            hdr = self._HDR[:self._typed]
            cursor = "_" if self._typed < len(self._HDR) else ""
            hdr_cx = lx + pw // 2
            cv.create_text(hdr_cx, py + 16, text=hdr + cursor,
                           font=("Consolas", 9, "bold"), fill=ACCENT, anchor="center",
                           width=pw - 20)

        # ── boot log (left panel) — clip text to panel width ───────────────────
        tx = lx + 14
        ty = py + 50          # below 34px header + 16px gap
        lh = 18
        max_text_w = pw - 28  # leave 14px margin each side
        all_lines = list(self._log_lines)
        if partial: all_lines.append(partial)
        max_show = (ph - 80) // lh
        for i, (txt, ck) in enumerate(all_lines[-max_show:]):
            col = self.COLORS.get(ck, FG2)
            cv.create_text(tx, ty + i * lh, text=txt,
                           font=("Consolas", 8), fill=col, anchor="w",
                           width=max_text_w)

        # ── right panel identity block ─────────────────────────────────────────
        if self._slide > 0.5:
            rc = rx + pw // 2
            rw = pw - 36   # usable text width within right panel
            cv.create_text(rc, py + 82,  text="SOLITON KIT",
                           font=("Consolas", 19, "bold"), fill=ACCENT, anchor="center",width=rw)
            cv.create_text(rc, py + 112, text=VERSION,
                           font=("Consolas", 11, "bold"), fill=ACCENT2, anchor="center",width=rw)
            cv.create_line(rx + 20, py + 132, rx + pw - 20, py + 132, fill=BORDER2)
            cv.create_text(rc, py + 154, text="SEO INTELLIGENCE TOOLKIT",
                           font=("Consolas", 8), fill=FG2, anchor="center",width=rw)
            cv.create_text(rc, py + 178, text="by  Solidsman  (Shak)",
                           font=("Consolas", 9), fill=FG3, anchor="center",width=rw)
            mods = ["Keyword Extractor", "On-Page Crawler",
                    "PageSpeed Monitor", "Keyword Density", "Schema Generator"]
            for i, m in enumerate(mods):
                my = py + 216 + i * 24
                cv.create_text(rx + 18, my, text=f"  {m}",
                               font=("Consolas", 9),
                               fill=FG2 if self._phase >= 3 else FG3, anchor="w",
                               width=pw-70)
                ready = self._phase >= 3 and self._line > 11 + i
                dot_col = SUCCESS if ready else FG3
                cv.create_text(rx + pw - 18, my,
                               text="READY" if ready else "......",
                               font=("Consolas", 9), fill=dot_col, anchor="e")

        # ── progress bar ──────────────────────────────────────────────────────
        if self._phase == 4:
            bx1 = lx + 14; bx2 = lx + pw - 14; by = py + ph - 28
            # label above bar, inside left panel
            cv.create_text(lx + pw//2, py + ph - 42, text="LAUNCHING..." if self._prog_val < 1.0 else "READY",
                           font=("Consolas", 8, "bold"), fill=SUCCESS, anchor="center",width=pw-28)
            cv.create_rectangle(bx1, by, bx2, by + 8, fill=BG3, outline=BORDER2)
            filled = bx1 + int((bx2 - bx1) * self._prog_val)
            if filled > bx1:
                cv.create_rectangle(bx1, by, filled, by + 8, fill=ACCENT, outline="")

        # outer border
        cv.create_rectangle(0, 0, W-1, H-1, fill="", outline=ACCENT3, width=1)
        # bottom bar
        cv.create_rectangle(0, H-22, W, H, fill="#000810", outline="")
        cv.create_text(14, H-11, text="CLICK OR PRESS ANY KEY TO SKIP",
                       font=("Consolas", 8), fill=FG3, anchor="w")
        cv.create_text(W-14, H-11, text=TODAY,
                       font=("Consolas", 8), fill=FG3, anchor="e")

    def _draw_panel(self, cv, x, y, w, h, left=True):
        cv.create_rectangle(x, y, x+w, y+h, fill=BG, outline="")
        cv.create_rectangle(x, y, x+w, y+h, fill="", outline=BORDER2)
        cv.create_rectangle(x, y, x+w, y+34, fill=HDRBG, outline="")
        cv.create_line(x, y+34, x+w, y+34, fill=BORDER2)
        cv.create_rectangle(x, y, x+w, y+2, fill=ACCENT2, outline="")
        label = "BOOT LOG" if left else "SYSTEM ID"
        cv.create_text(x+12, y+17, text=label,
                       font=("Consolas", 9, "bold"), fill=ACCENT, anchor="w",
                       width=w-24)

    def _finish(self):
        if self._done: return
        self._done = True
        self.after(120, lambda: (self.destroy(), self._on_done()))

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL: KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════
class KeywordPanel(tk.Frame):
    def __init__(self,parent,get_key,cfg):
        super().__init__(parent,bg=BG)
        self._get_key=get_key; self._cfg=cfg
        self._data=[]; self._sort_rev=True; self._build()

    def _build(self):
        self.columnconfigure(0,weight=1); self.rowconfigure(3,weight=1)
        cf=tk.Frame(self,bg=BG2); cf.grid(row=0,column=0,sticky="ew")
        ci=tk.Frame(cf,bg=BG2); ci.pack(fill="x",padx=14,pady=10)
        ci.columnconfigure(1,weight=1)
        _lbl(ci,"KEYWORD").grid(row=0,column=0,padx=(0,8),sticky="w")
        self._kw=_entry(ci,self._cfg.get("kw_last",""),width=30)
        self._kw.grid(row=0,column=1,sticky="ew",padx=(0,12),ipady=4)
        self._kw.bind("<Return>",lambda _:self.run())
        _lbl(ci,"COUNTRY").grid(row=0,column=2,padx=(0,6),sticky="w")
        self._country=tk.StringVar(value=C_TO_LBL.get(self._cfg.get("country","in"),"India"))
        _combo(ci,self._country,C_LABELS,10).grid(row=0,column=3,padx=(0,10))
        _lbl(ci,"LANG").grid(row=0,column=4,padx=(0,6),sticky="w")
        self._lang=tk.StringVar(value=self._cfg.get("language","en"))
        _combo(ci,self._lang,LANGUAGES,5).grid(row=0,column=5,padx=(0,10))
        self._var_flag=tk.BooleanVar(value=True)
        ttk.Checkbutton(ci,text="VARIATIONS",variable=self._var_flag,
                        style="TCheckbutton").grid(row=0,column=6,padx=(0,10))
        bf=tk.Frame(ci,bg=BG2); bf.grid(row=0,column=7,sticky="e")
        _btn(bf,"RUN",self.run).pack(side="left",padx=(0,4))
        _btn(bf,"CSV",self._export,bg="#054D36").pack(side="left",padx=(0,4))
        _btn(bf,"CLEAR",self._clear,bg="#3A0A0A").pack(side="left")
        self._prog=_prog(self); self._prog.grid(row=1,column=0,sticky="ew"); self._prog.grid_remove()
        fb=tk.Frame(self,bg=BG); fb.grid(row=2,column=0,sticky="ew",padx=10,pady=(6,2))
        fb.columnconfigure(5,weight=1)
        self._status=tk.Label(fb,text="Enter a keyword and press RUN.",
                              font=("Consolas",8),fg=FG3,bg=BG,anchor="w")
        self._status.grid(row=0,column=0,columnspan=2,sticky="w")
        _lbl(fb,"FILTER").grid(row=0,column=2,padx=(14,4))
        self._flt=_entry(fb,"",20); self._flt.grid(row=0,column=3,padx=(0,8))
        self._flt.bind("<KeyRelease>",lambda _:self._apply_filter())
        _lbl(fb,"SOURCE").grid(row=0,column=4,padx=(0,4))
        self._src_var=tk.StringVar(value="All")
        _combo(fb,self._src_var,["All"]+list(SOURCE_ORDER.keys()),14).grid(row=0,column=5,sticky="w")
        self._src_var.trace_add("write",lambda *_:self._apply_filter())
        self._cnt=tk.Label(fb,text="0 keywords",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG)
        self._cnt.grid(row=0,column=6,padx=(10,0),sticky="e")
        cols=("Keyword","Source","Words","Score","Query Used")
        widths={"Keyword":380,"Source":150,"Words":58,"Score":62,"Query Used":180}
        tf,self._tree=_mktree(self,cols,widths,"Keyword")
        tf.grid(row=3,column=0,sticky="nsew")
        for c in cols: self._tree.heading(c,text=c,command=lambda c=c:self._sort(c))
        self._tree.tag_configure("seed",background="#001828",foreground="#00AAFF")
        self._tree.tag_configure("paa", background="#041404",foreground="#00EE88")
        self._tree.tag_configure("rel", background="#030F1E",foreground="#60A8FF")
        self._tree.tag_configure("title",background=BG3,    foreground=FG)
        self._tree.tag_configure("feat",background="#181200",foreground="#FFD000")
        self._tree.tag_configure("story",background="#0E0818",foreground="#BB80FF")
        self._tree.tag_configure("kg",  background="#080E1A",foreground="#00CCFF")
        self._tree.tag_configure("alt", background=BG4,     foreground=FG2)
        rcm=tk.Menu(self,tearoff=0,bg=BG2,fg=FG,activebackground=ACCENT3,
                    activeforeground="#FFF",font=("Segoe UI",9))
        rcm.add_command(label="Copy Keyword",    command=self._copy_sel)
        rcm.add_command(label="Copy All Visible",command=self._copy_all)
        self._tree.bind("<Button-3>",lambda e:_popup(self,rcm,e))

    def _tag(self,src):
        return {"Seed Keyword":"seed","People Also Ask":"paa","Related Search":"rel",
                "Organic Title":"title","Featured Snippet":"feat","Top Stories":"story",
                "Knowledge Graph":"kg"}.get(src,"alt")

    def run(self):
        kw=self._kw.get().strip(); sk=self._get_key()
        if not kw: messagebox.showwarning("Input","Enter a keyword first."); return
        if not sk: return
        gl=C_TO_CODE.get(self._country.get(),"in"); hl=self._lang.get()
        queries=[kw]+([f"{kw} tips",f"{kw} guide",f"how to {kw}",f"best {kw}"]
                      if self._var_flag.get() else [])
        self._data=[]; self._tree.delete(*self._tree.get_children())
        self._cnt.config(text="0 keywords")
        self._prog.grid(); self._prog.start(8)
        self._status.config(text="Starting...",fg=ACCENT)
        def worker():
            seen,out=set(),[]
            for i,q in enumerate(queries,1):
                self.after(0,lambda q=q,i=i:self._status.config(
                    text=f"[{i}/{len(queries)}]  {q}",fg=ACCENT))
                try:
                    data=_serper(q,sk,gl=gl,hl=hl,num=10)
                    _extract_keywords(data,q,seen,out)
                    self.after(0,lambda n=len(out):self._cnt.config(text=f"{n} keywords"))
                except Exception as ex:
                    err=str(ex)
                    self.after(0,lambda e=err:self._status.config(text=f"Error: {e}",fg=WARNING))
            out.sort(key=lambda x:(SOURCE_ORDER.get(x["source"],9),-x["score"]))
            self._data=out; self.after(0,self._populate)
            self.after(0,self._prog.stop); self.after(0,self._prog.grid_remove)
            n=len(out)
            self.after(0,lambda:self._status.config(
                text=f"{n} unique keywords extracted." if n else "0 results. Check API key.",
                fg=SUCCESS if n else WARNING))
        threading.Thread(target=worker,daemon=True).start()

    def _populate(self,data=None):
        self._tree.delete(*self._tree.get_children())
        rows=data if data is not None else self._data
        for i,kw in enumerate(rows):
            tag=self._tag(kw["source"])
            if tag=="alt" and i%2==0: tag="title"
            self._tree.insert("","end",values=(kw["keyword"],kw["source"],
                kw["words"],kw["score"],kw["query_used"]),tags=(tag,))
        self._cnt.config(text=f"{len(rows)} keywords")

    def _clear(self):
        self._data=[]; self._tree.delete(*self._tree.get_children())
        self._cnt.config(text="0 keywords"); self._status.config(text="Cleared.",fg=FG3)

    def _apply_filter(self):
        tf=self._flt.get().lower(); src=self._src_var.get()
        self._populate([k for k in self._data
                        if (not tf or tf in k["keyword"].lower())
                        and (src=="All" or k["source"]==src)])

    def _sort(self,col):
        km={"Keyword":"keyword","Source":"source","Words":"words",
            "Score":"score","Query Used":"query_used"}
        self._sort_rev=not self._sort_rev
        self._data.sort(key=lambda x:x[km.get(col,"score")],reverse=self._sort_rev)
        self._apply_filter()

    def _export(self):
        if not self._data: messagebox.showinfo("No data","Run extraction first."); return
        p=filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV","*.csv")],initialfile="soliton_keywords.csv")
        if not p: return
        with open(p,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["keyword","source","words","length","score","query_used"])
            w.writeheader(); w.writerows(self._data)
        messagebox.showinfo("Exported",f"Saved:\n{p}")

    def _copy_sel(self):
        sel=self._tree.selection()
        if sel: self.clipboard_clear(); self.clipboard_append(self._tree.item(sel[0],"values")[0])

    def _copy_all(self):
        lines=[self._tree.item(i,"values")[0] for i in self._tree.get_children()]
        self.clipboard_clear(); self.clipboard_append("\n".join(lines))
        messagebox.showinfo("Copied",f"{len(lines)} keywords copied.")

    def get_state(self):
        return {"kw_last":self._kw.get().strip(),
                "country":C_TO_CODE.get(self._country.get(),"in"),
                "language":self._lang.get()}

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL: CRAWLER
# ═══════════════════════════════════════════════════════════════════════════════
class CrawlerPanel(tk.Frame):
    def __init__(self,parent,cfg):
        super().__init__(parent,bg=BG); self._cfg=cfg; self._result=None; self._build()

    def _build(self):
        self.columnconfigure(0,weight=1); self.rowconfigure(2,weight=1)
        cf=tk.Frame(self,bg=BG2); cf.grid(row=0,column=0,sticky="ew")
        ci=tk.Frame(cf,bg=BG2); ci.pack(fill="x",padx=14,pady=10); ci.columnconfigure(1,weight=1)
        _lbl(ci,"URL").grid(row=0,column=0,padx=(0,8),sticky="w")
        self._url=_entry(ci,self._cfg.get("crawl_last","https://"),width=60)
        self._url.grid(row=0,column=1,sticky="ew",padx=(0,12),ipady=4)
        self._url.bind("<Return>",lambda _:self.run())
        bf=tk.Frame(ci,bg=BG2); bf.grid(row=0,column=2,sticky="e")
        _btn(bf,"CRAWL",self.run).pack(side="left",padx=(0,4))
        _btn(bf,"CLEAR",self._clear,bg="#3A0A0A").pack(side="left")
        self._prog=_prog(self); self._prog.grid(row=1,column=0,sticky="ew"); self._prog.grid_remove()
        content=tk.Frame(self,bg=BG); content.grid(row=2,column=0,sticky="nsew")
        content.rowconfigure(0,weight=1); content.columnconfigure(0,weight=3); content.columnconfigure(1,weight=2)
        left=tk.Frame(content,bg=BG); left.grid(row=0,column=0,sticky="nsew",padx=(0,1))
        left.rowconfigure(1,weight=1); left.columnconfigure(0,weight=1)
        lh=tk.Frame(left,bg=BG3); lh.grid(row=0,column=0,sticky="ew")
        tk.Label(lh,text="  AUDIT RESULTS",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(side="left")
        self._status=tk.Label(lh,text="Enter URL and press CRAWL.",
                              font=("Consolas",8),fg=FG3,bg=BG3,anchor="e")
        self._status.pack(side="right",padx=10)
        cols=("Category","Check","Value","Status")
        widths={"Category":115,"Check":190,"Value":360,"Status":42}
        tf,self._tree=_mktree(left,cols,widths,"Value"); tf.grid(row=1,column=0,sticky="nsew")
        self._tree.tag_configure("section",background="#00060F",foreground=ACCENT,
                                 font=("Consolas",9,"bold"))
        self._tree.tag_configure("ok",   background=BG3,foreground=SUCCESS)
        self._tree.tag_configure("warn", background=BG3,foreground=WARNING)
        self._tree.tag_configure("bad",  background=BG3,foreground=DANGER)
        self._tree.tag_configure("info", background=BG4,foreground=FG2)
        self._tree.tag_configure("sub",  background=BG5,foreground=FG3)
        self._tree.bind("<Double-1>",self._open_link)
        right=tk.Frame(content,bg=BG2); right.grid(row=0,column=1,sticky="nsew")
        right.rowconfigure(1,weight=1); right.columnconfigure(0,weight=1)
        rh=tk.Frame(right,bg=BG3); rh.grid(row=0,column=0,sticky="ew")
        tk.Label(rh,text="  RAW DETAIL",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(side="left")
        _btn(rh,"X",self._clear_log,bg=BG3,small=True).pack(side="right",padx=6,pady=4)
        self._log=scrolledtext.ScrolledText(right,font=("Consolas",8),bg=BG2,fg=FG2,
                                            relief="flat",highlightthickness=0,wrap="word",
                                            insertbackground=ACCENT,padx=8,pady=8,state="disabled")
        self._log.grid(row=1,column=0,sticky="nsew")
        self._bar=tk.Label(self,text="No crawl yet.",font=("Consolas",8),fg=FG3,bg=BG,anchor="w")
        self._bar.grid(row=3,column=0,sticky="ew",padx=10,pady=(2,4))

    def run(self):
        url=self._url.get().strip()
        if not url or url in ("https://","http://"): messagebox.showwarning("Input","Enter a URL."); return
        if not url.startswith("http"): url="https://"+url; self._url.delete(0,"end"); self._url.insert(0,url)
        self._tree.delete(*self._tree.get_children()); self._clear_log()
        self._prog.grid(); self._prog.start(8)
        self._status.config(text="Crawling...",fg=ACCENT)
        self._bar.config(text=f"Fetching  {url}",fg=ACCENT)
        self._log_w(f"TARGET  : {url}\n{'─'*50}")
        def worker():
            try:
                r=_crawl(url); self._result=r; self.after(0,lambda:self._render(r))
            except Exception as ex:
                err=str(ex)
                self.after(0,lambda e=err:self._status.config(text=f"Error: {e}",fg=DANGER))
                self.after(0,lambda e=err:self._bar.config(text=f"Error: {e}",fg=DANGER))
                self.after(0,lambda e=err:self._log_w(f"ERROR: {e}"))
            finally:
                self.after(0,self._prog.stop); self.after(0,self._prog.grid_remove)
        threading.Thread(target=worker,daemon=True).start()

    def _render(self,r):
        tv=self._tree; tv.delete(*tv.get_children())
        def sec(n): tv.insert("","end",values=(f"  {n}","","",""),tags=("section",))
        def row(cat,chk,val,tag="info"): tv.insert("","end",values=(cat,chk,str(val)[:200],""),tags=(tag,))
        def srow(cat,chk,val,good,ok_h="",wn_h=""):
            tag="ok" if good else "warn"; icon="OK" if good else "!!"
            hint=ok_h if good else wn_h
            tv.insert("","end",values=(cat,chk,f"{val}  {hint}"[:200],icon),tags=(tag,))
        sec("OVERVIEW")
        sc=r["status_code"]
        row("Response","HTTP Status",sc,"ok" if sc==200 else("warn" if sc<400 else "bad"))
        row("Speed","Load Time",f"{r['load_ms']} ms","ok" if r["load_ms"]<1500 else "warn")
        row("Page","Size",f"{r['page_size_kb']} KB","info")
        srow("HTTPS","Secure","HTTPS" if r["https_ok"] else "HTTP",r["https_ok"],"","Not using HTTPS!")
        if r["has_mixed"]: row("HTTPS","Mixed Content","HTTP resources on HTTPS page","warn")
        row("URL","Final URL",r["url"][:90],"info")
        if r["redirected"]: row("URL","Redirect","Page was redirected","warn")
        if r.get("server"): row("Server","Server",r["server"],"info")
        if r.get("cache_control"): row("Cache","Cache-Control",r["cache_control"],"info")
        sec("META TAGS")
        t=r["title_len"]
        srow("Title","Present",r["title"][:120] if r["title"] else "(missing)",bool(r["title"]),f"[{t} chars]","MISSING!")
        srow("Title","Length 50-60",f"{t} chars",50<=t<=60,"ideal","too short" if t<50 else "too long")
        d=r["desc_len"]
        srow("Description","Present",r["description"][:120] if r["description"] else "(missing)",bool(r["description"]),f"[{d} chars]","MISSING!")
        srow("Description","Length 120-158",f"{d} chars",120<=d<=158,"ideal","too short" if d<120 else "too long")
        srow("Canonical","Present",r["canonical"] if r["canonical"] else "(missing)",bool(r["canonical"]),"","Missing!")
        row("Robots","Meta Robots",r["robots_meta"] or "not set","info")
        srow("Viewport","Mobile Ready",r["viewport"] if r["viewport"] else "(missing)",bool(r["viewport"]),"","Missing!")
        srow("Charset","Declared",r["charset"] if r["charset"] else "(missing)",bool(r["charset"]),"","Not declared!")
        if r["hreflang"]: row("Hreflang","Langs found",", ".join(r["hreflang"][:5]),"info")
        sec("HEADING STRUCTURE")
        srow("H1",f"Count: {len(r['h1'])} (ideal=1)",r["h1"][0][:120] if r["h1"] else "(none)",
             len(r["h1"])==1,"","Must have exactly ONE H1!")
        for txt in r["h1"][1:]: tv.insert("","end",values=("","Extra H1",txt[:120],"!!"),tags=("warn",))
        row("H2",f"Count: {len(r['h2'])}",", ".join(r["h2"][:5])[:200],"info")
        row("H3",f"Count: {len(r['h3'])}",", ".join(r["h3"][:5])[:200],"info")
        wc=r["word_count"]
        srow("Content","Word Count",f"{wc} words",wc>=300,"","Thin content!")
        row("Content","Avg Sentence",f"{r['avg_sentence_words']} words/sentence","info")
        sec("IMAGES")
        row("Images","Total",f"{r['img_total']} images","info")
        no=r["img_no_alt"]
        srow("Images","Missing ALT",f"{no} missing alt",no==0,"All OK","Fix "+str(no)+" images!")
        for src in r["img_no_alt_list"][:5]: tv.insert("","end",values=("","No ALT",src[:100],"!!"),tags=("sub",))
        if no>5: tv.insert("","end",values=("","",f"...and {no-5} more",""),tags=("sub",))
        sec("LINKS")
        row("Links","Internal",f"{len(r['internal_links'])} links","info")
        row("Links","External",f"{len(r['external_links'])} links","info")
        row("Links","Nofollow",f"{r['nofollow_count']} links","info")
        for lnk in r["internal_links"][:4]:
            tv.insert("","end",values=("",lnk["text"][:40] or "(no text)",lnk["url"][:90],"->"),tags=("sub",))
        if len(r["internal_links"])>4:
            tv.insert("","end",values=("","",f"...and {len(r['internal_links'])-4} more",""),tags=("sub",))
        sec("STRUCTURED DATA")
        if r["schema_types"]:
            for st in r["schema_types"]: row("Schema","Type detected",st,"ok")
        else:
            srow("Schema","JSON-LD","None detected",False,"","No structured data!")
        srow("Schema","FAQPage","Found" if r["has_faq"] else "Not found",r["has_faq"])
        srow("Schema","BreadcrumbList","Found" if r["has_breadcrumb"] else "Not found",r["has_breadcrumb"])
        srow("Schema","Article Schema","Found" if r["has_article"] else "Not found",r["has_article"])
        sec("SOCIAL META")
        for k,val in r["social"].items():
            row("Social",k,val[:160] if val else "(missing)","ok" if val else "warn")
        self._status.config(text="Crawl complete",fg=SUCCESS)
        self._bar.config(text=(f"{r['url']}  |  {r['status_code']}  |  {r['load_ms']} ms  |  "
                               f"{r['word_count']} words  |  {r['page_size_kb']} KB  |  "
                               f"{r['img_total']} imgs ({r['img_no_alt']} no-alt)"),fg=SUCCESS)
        self._log_w(f"STATUS  : {r['status_code']}\nHTTPS   : {'yes' if r['https_ok'] else 'NO'}\n"
                    f"LOAD    : {r['load_ms']} ms\nSIZE    : {r['page_size_kb']} KB\n"
                    f"WORDS   : {r['word_count']}\nTITLE   : {r['title']} [{r['title_len']}]\n"
                    f"DESC    : {r['description'][:100]} [{r['desc_len']}]\n"
                    f"CANON   : {r['canonical'] or 'none'}\n{'─'*50}\n"
                    f"H1s ({len(r['h1'])}): {' | '.join(r['h1'][:3])}\n"
                    f"H2s ({len(r['h2'])}): {' | '.join(r['h2'][:3])}\n{'─'*50}\n"
                    f"IMGS    : {r['img_total']} total, {r['img_no_alt']} no-alt\n"
                    f"LINKS   : {len(r['internal_links'])} int, {len(r['external_links'])} ext\n"
                    f"SCHEMA  : {', '.join(r['schema_types']) or 'none'}")

    def _open_link(self,_):
        sel=self._tree.selection()
        if sel:
            val=self._tree.item(sel[0],"values")[2]
            if val.startswith("http"): webbrowser.open(val)

    def _clear(self):
        self._result=None; self._tree.delete(*self._tree.get_children()); self._clear_log()
        self._status.config(text="Cleared.",fg=FG3); self._bar.config(text="No crawl yet.",fg=FG3)

    def _clear_log(self):
        self._log.configure(state="normal"); self._log.delete("1.0","end")
        self._log.configure(state="disabled")

    def _log_w(self,msg):
        self._log.configure(state="normal"); self._log.insert("end",msg+"\n")
        self._log.see("end"); self._log.configure(state="disabled")

    def get_state(self): return {"crawl_last":self._url.get().strip()}

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL: PAGESPEED
# ═══════════════════════════════════════════════════════════════════════════════
class PageSpeedPanel(tk.Frame):
    def __init__(self,parent,get_key,cfg):
        super().__init__(parent,bg=BG); self._get_key=get_key; self._cfg=cfg; self._build()

    def _build(self):
        self.columnconfigure(0,weight=1); self.rowconfigure(2,weight=1)
        cf=tk.Frame(self,bg=BG2); cf.grid(row=0,column=0,sticky="ew")
        ci=tk.Frame(cf,bg=BG2); ci.pack(fill="x",padx=14,pady=10); ci.columnconfigure(1,weight=1)
        _lbl(ci,"URL").grid(row=0,column=0,padx=(0,8),sticky="w")
        self._url=_entry(ci,self._cfg.get("ps_last_url","https://"),width=60)
        self._url.grid(row=0,column=1,sticky="ew",padx=(0,12),ipady=4)
        self._url.bind("<Return>",lambda _:self.run())
        _lbl(ci,"STRATEGY").grid(row=0,column=2,padx=(0,6),sticky="w")
        self._strategy=tk.StringVar(value=self._cfg.get("strategy","Both"))
        _combo(ci,self._strategy,["mobile","desktop","Both"],9).grid(row=0,column=3,padx=(0,12))
        bf=tk.Frame(ci,bg=BG2); bf.grid(row=0,column=4,sticky="e")
        _btn(bf,"ANALYZE",self.run).pack(side="left",padx=(0,4))
        _btn(bf,"CLEAR",self._clear,bg="#3A0A0A").pack(side="left")
        self._prog=_prog(self); self._prog.grid(row=1,column=0,sticky="ew"); self._prog.grid_remove()
        content=tk.Frame(self,bg=BG); content.grid(row=2,column=0,sticky="nsew")
        content.rowconfigure(0,weight=1); content.columnconfigure(0,weight=4); content.columnconfigure(1,weight=1)
        left=tk.Frame(content,bg=BG); left.grid(row=0,column=0,sticky="nsew")
        left.rowconfigure(0,weight=1); left.columnconfigure(0,weight=1)
        self._cv=tk.Canvas(left,bg=BG,highlightthickness=0,bd=0)
        self._cv.grid(row=0,column=0,sticky="nsew")
        cvs=ttk.Scrollbar(left,orient="vertical",style="T.Vertical.TScrollbar",command=self._cv.yview)
        cvs.grid(row=0,column=1,sticky="ns"); self._cv.configure(yscrollcommand=cvs.set)
        self._cards=tk.Frame(self._cv,bg=BG)
        self._win=self._cv.create_window((0,0),window=self._cards,anchor="nw")
        self._cards.bind("<Configure>",self._on_cards_cfg)
        self._cv.bind("<Configure>",lambda e:self._cv.itemconfig(self._win,width=e.width))
        self._cv.bind("<MouseWheel>",lambda e:self._cv.yview_scroll(-1*(e.delta//120),"units"))
        right=tk.Frame(content,bg=BG2); right.grid(row=0,column=1,sticky="nsew",padx=(2,0))
        right.rowconfigure(1,weight=1); right.columnconfigure(0,weight=1)
        rh=tk.Frame(right,bg=BG3); rh.grid(row=0,column=0,sticky="ew")
        tk.Label(rh,text="  ANALYSIS LOG",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(side="left")
        _btn(rh,"X",self._clear_log,bg=BG3,small=True).pack(side="right",padx=6,pady=4)
        self._log=scrolledtext.ScrolledText(right,font=("Consolas",8),bg=BG2,fg=FG2,
                                            relief="flat",highlightthickness=0,wrap="word",
                                            insertbackground=ACCENT,padx=8,pady=8,state="disabled")
        self._log.grid(row=1,column=0,sticky="nsew")
        self._status=tk.Label(self,text="Enter a URL and press ANALYZE.",
                              font=("Consolas",8),fg=FG3,bg=BG,anchor="w")
        self._status.grid(row=3,column=0,sticky="ew",padx=10,pady=(2,4))

    def _on_cards_cfg(self,event=None):
        self._cv.configure(scrollregion=self._cv.bbox("all"))
        # update wraplength on opportunity title labels once width is known
        try:
            cw=self._cv.winfo_width()
            children=[c for c in self._cards.winfo_children()]
            n=max(1,len(children))
            card_inner=max(80,(cw//n)-80)
            for widget in children:
                self._set_wraplength(widget,card_inner)
        except Exception: pass

    def _set_wraplength(self,widget,wl):
        try:
            for child in widget.winfo_children():
                if isinstance(child,tk.Label):
                    try:
                        if child.cget("wraplength")==1:
                            child.configure(wraplength=wl)
                    except Exception: pass
                self._set_wraplength(child,wl)
        except Exception: pass

    def run(self):
        url=self._url.get().strip()
        if not url or url in ("https://","http://",""):
            messagebox.showwarning("Input","Enter a URL."); return
        if not url.startswith("http"): url="https://"+url; self._url.delete(0,"end"); self._url.insert(0,url)
        pk=self._get_key()
        if not pk: return
        strats=["mobile","desktop"] if self._strategy.get()=="Both" else [self._strategy.get()]
        self._prog.grid(); self._prog.start(8)
        self._status.config(text="Contacting PageSpeed API...",fg=ACCENT)
        self._clear_cards(); self._clear_log()
        self._log_w(f"URL   : {url}\nMODE  : {self._strategy.get()}\n{'─'*40}")
        def worker():
            results=[]
            for s in strats:
                self.after(0,lambda s=s:self._status.config(text=f"[{s.upper()}] Fetching...",fg=ACCENT))
                self.after(0,lambda s=s:self._log_w(f"  {s.upper()}..."))
                try:
                    data=_fetch_ps(url,pk,s); parsed=_parse_ps(data,s); results.append(parsed)
                    score=parsed["performance"]
                    self.after(0,lambda sc=score:self._log_w(f"  Score : {sc}/100"))
                    for m,val,_ in parsed["metrics"]:
                        self.after(0,lambda m=m,val=val:self._log_w(f"  {m:<12} {val}"))
                    self.after(0,lambda:self._log_w("─"*40))
                except Exception as ex:
                    err=str(ex)
                    self.after(0,lambda e=err,s=s:self._log_w(f"ERROR [{s}]: {e}"))
                    self.after(0,lambda e=err:self._status.config(text=f"Error: {e}",fg=DANGER))
            self.after(0,lambda:self._draw_cards(results))
            self.after(0,self._prog.stop); self.after(0,self._prog.grid_remove)
            self.after(0,lambda:self._status.config(text=f"Done  {len(results)} result(s).",fg=SUCCESS))
        threading.Thread(target=worker,daemon=True).start()

    def _clear_cards(self):
        for w in self._cards.winfo_children(): w.destroy()

    def _clear(self):
        self._clear_cards(); self._clear_log(); self._status.config(text="Cleared.",fg=FG3)

    def _draw_cards(self,results):
        self._clear_cards()
        row=tk.Frame(self._cards,bg=BG); row.pack(fill="both",expand=True,padx=14,pady=14)
        for i,r in enumerate(results):
            col=tk.Frame(row,bg=BG)
            col.pack(side="left",fill="both",expand=True,padx=(0,16 if i<len(results)-1 else 0))
            self._draw_card(col,r)

    def _draw_card(self,parent,r):
        border=tk.Frame(parent,bg=BORDER2); border.pack(fill="both",expand=True,pady=2)
        card=tk.Frame(border,bg=BG5); card.pack(fill="both",expand=True,padx=1,pady=(0,1))
        mob=r["strategy"]=="MOBILE"
        icon_str="\u25a3 M" if mob else "\u25a3 D"
        hbg="#000A1E" if mob else "#060012"
        h=tk.Frame(card,bg=hbg); h.pack(fill="x")
        tk.Label(h,text=f"  {icon_str}  {r['strategy']}",font=("Consolas",11,"bold"),
                 fg=ACCENT,bg=hbg,pady=10,padx=10).pack(side="left")
        tk.Label(h,text=f"{r['performance']}/100",font=("Consolas",12,"bold"),
                 fg=r["perf_color"],bg=hbg,padx=14).pack(side="right")
        _hline(card,BORDER).pack(fill="x")
        # Score category boxes
        sf=tk.Frame(card,bg=BG5); sf.pack(fill="x",padx=10,pady=(10,0))
        for i,(cname,cscore,cc) in enumerate(r["categories"]):
            pf=tk.Frame(sf,bg=BG4); pf.pack(side="left",fill="x",expand=True,
                                             padx=(0,3) if i<len(r["categories"])-1 else 0)
            tk.Label(pf,text=str(cscore),font=("Consolas",13,"bold"),fg=cc,bg=BG4,pady=6).pack()
            tk.Label(pf,text=cname,font=("Segoe UI",7),fg=FG3,bg=BG4).pack(pady=(0,6))
        # Donut ring
        SZ,PAD=156,14
        gf=tk.Frame(card,bg=BG5); gf.pack(pady=(14,4))
        cv=tk.Canvas(gf,width=SZ,height=SZ,bg=BG5,highlightthickness=0); cv.pack()
        score=r["performance"]; color=r["perf_color"]
        cx=cy=SZ//2; R=(SZ-PAD*2)//2; Ri=R-16
        self._draw_ring(cv,cx,cy,R,Ri,0,360,BG3)
        if score>0: self._draw_ring(cv,cx,cy,R,Ri,0,min(359.9,score/100*360),color)
        cv.create_text(cx,cy-11,text=str(score),font=("Consolas",26,"bold"),fill=color)
        cv.create_text(cx,cy+16,text="/ 100",font=("Segoe UI",9),fill=FG3)
        tk.Label(card,text="Performance Score",font=("Segoe UI",8),fg=FG3,bg=BG5).pack(pady=(0,10))
        # Metrics
        _hline(card,BORDER).pack(fill="x",padx=12)
        mf=tk.Frame(card,bg=BG5); mf.pack(fill="x",padx=14,pady=10)
        for metric,val,sc in r["metrics"]:
            dot=_sc(sc); mr=tk.Frame(mf,bg=BG5); mr.pack(fill="x",pady=2)
            tk.Label(mr,text=metric,font=("Segoe UI",9),fg=FG2,bg=BG5,anchor="w",width=6).pack(side="left")
            tk.Label(mr,text="\u25cf",font=("Consolas",7),fg=dot,bg=BG5).pack(side="right",padx=(4,2))
            tk.Label(mr,text=val,font=("Consolas",9,"bold"),fg=dot,bg=BG5).pack(side="right")
        # Opportunities - grid layout to prevent overflow
        if r.get("opportunities"):
            _hline(card,BORDER).pack(fill="x",padx=12)
            tk.Label(card,text="  \u26a0 OPPORTUNITIES",font=("Consolas",8,"bold"),
                     fg=WARNING,bg=BG5,anchor="w").pack(fill="x",padx=12,pady=(8,2))
            of=tk.Frame(card,bg=BG5); of.pack(fill="x",padx=12,pady=(0,10))
            of.columnconfigure(1,weight=1)
            for row_idx,(title,disp) in enumerate(r["opportunities"][:5]):
                tk.Label(of,text="\u0021",font=("Consolas",8,"bold"),fg=WARNING,bg=BG5,
                         anchor="w",width=2).grid(row=row_idx,column=0,sticky="w",pady=2)
                tk.Label(of,text=title,font=("Segoe UI",8),fg=FG2,bg=BG5,
                         anchor="w",wraplength=1).grid(row=row_idx,column=1,sticky="ew",padx=(2,6),pady=2)
                tk.Label(of,text=disp,font=("Consolas",8,"bold"),fg=DANGER,bg=BG5,
                         anchor="e").grid(row=row_idx,column=2,sticky="e",pady=2)
        _hline(card,BORDER).pack(fill="x",padx=12)
        leg=tk.Frame(card,bg=BG5); leg.pack(pady=(6,14))
        for c,label in [(SUCCESS,"\u2265 90 Good"),(WARNING,"50\u201389 Fair"),(DANGER,"< 50 Poor")]:
            tk.Label(leg,text=f" {label}",font=("Consolas",8),fg=c,bg=BG5).pack(side="left",padx=5)

    @staticmethod
    def _draw_ring(cv,cx,cy,R_out,R_in,start_deg,extent_deg,color,steps=120):
        if extent_deg<=0: return
        extent_deg=min(extent_deg,359.99)
        n=max(4,int(steps*extent_deg/360)); pts=[]
        for i in range(n+1):
            a=math.radians(start_deg-90+extent_deg*i/n)
            pts.append((cx+R_out*math.cos(a),cy+R_out*math.sin(a)))
        for i in range(n+1):
            a=math.radians(start_deg-90+extent_deg*(n-i)/n)
            pts.append((cx+R_in*math.cos(a),cy+R_in*math.sin(a)))
        flat=[c for pt in pts for c in pt]
        cv.create_polygon(flat,fill=color,outline=color,smooth=False)

    def _clear_log(self):
        self._log.configure(state="normal"); self._log.delete("1.0","end")
        self._log.configure(state="disabled")

    def _log_w(self,msg):
        self._log.configure(state="normal"); self._log.insert("end",msg+"\n")
        self._log.see("end"); self._log.configure(state="disabled")

    def get_state(self):
        return {"ps_last_url":self._url.get().strip(),"strategy":self._strategy.get()}

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL: DENSITY
# ═══════════════════════════════════════════════════════════════════════════════
class DensityPanel(tk.Frame):
    def __init__(self,parent,get_key,cfg):
        super().__init__(parent,bg=BG)
        self._get_key=get_key; self._cfg=cfg
        self._all_rows=[]; self._sort_rev=True; self._build()

    def _build(self):
        self.columnconfigure(0,weight=1); self.rowconfigure(2,weight=1)
        cf=tk.Frame(self,bg=BG2); cf.grid(row=0,column=0,sticky="ew")
        ci=tk.Frame(cf,bg=BG2); ci.pack(fill="x",padx=14,pady=10)
        ci.columnconfigure(1,weight=2); ci.columnconfigure(3,weight=1)
        _lbl(ci,"URL").grid(row=0,column=0,padx=(0,8),sticky="w")
        self._url=_entry(ci,self._cfg.get("density_url","https://"),width=44)
        self._url.grid(row=0,column=1,sticky="ew",padx=(0,12),ipady=4)
        self._url.bind("<Return>",lambda _:self.run())
        _lbl(ci,"FOCUS KEYWORD").grid(row=0,column=2,padx=(0,8),sticky="w")
        self._kw=_entry(ci,self._cfg.get("density_kw",""),width=22)
        self._kw.grid(row=0,column=3,sticky="ew",padx=(0,12),ipady=4)
        self._kw.bind("<Return>",lambda _:self.run())
        self._comp_flag=tk.BooleanVar(value=False)
        ttk.Checkbutton(ci,text="SERP COMPARE",variable=self._comp_flag,
                        style="TCheckbutton").grid(row=0,column=4,padx=(0,10))
        bf=tk.Frame(ci,bg=BG2); bf.grid(row=0,column=5,sticky="e")
        _btn(bf,"ANALYZE",self.run).pack(side="left",padx=(0,4))
        _btn(bf,"CSV",self._export,bg="#054D36").pack(side="left",padx=(0,4))
        _btn(bf,"CLEAR",self._clear,bg="#3A0A0A").pack(side="left")
        self._prog=_prog(self); self._prog.grid(row=1,column=0,sticky="ew"); self._prog.grid_remove()
        content=tk.Frame(self,bg=BG); content.grid(row=2,column=0,sticky="nsew")
        content.rowconfigure(0,weight=1); content.columnconfigure(0,weight=3); content.columnconfigure(1,weight=1)
        left=tk.Frame(content,bg=BG); left.grid(row=0,column=0,sticky="nsew",padx=(0,2))
        left.rowconfigure(1,weight=1); left.columnconfigure(0,weight=1)
        fbar=tk.Frame(left,bg=BG3); fbar.grid(row=0,column=0,sticky="ew")
        tk.Label(fbar,text="  DENSITY TABLE",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(side="left")
        tk.Label(fbar,text="SHOW:",font=("Consolas",8),fg=FG2,bg=BG3).pack(side="left")
        self._ngram_var=tk.StringVar(value="All")
        _combo(fbar,self._ngram_var,["All","1-gram","2-gram","3-gram"],8).pack(side="left",padx=(0,10))
        self._ngram_var.trace_add("write",lambda *_:self._apply_filter())
        tk.Label(fbar,text="FILTER:",font=("Consolas",8),fg=FG2,bg=BG3).pack(side="left")
        self._flt=_entry(fbar,"",16); self._flt.pack(side="left",padx=(0,10),ipady=2)
        self._flt.bind("<KeyRelease>",lambda _:self._apply_filter())
        self._cnt_lbl=tk.Label(fbar,text="",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3)
        self._cnt_lbl.pack(side="right",padx=10)
        self._status=tk.Label(fbar,text="Enter URL and press ANALYZE.",
                              font=("Consolas",8),fg=FG3,bg=BG3,anchor="e")
        self._status.pack(side="right",padx=10)
        cols=("Phrase","N-gram","Count","Density %","Assessment")
        widths={"Phrase":310,"N-gram":68,"Count":68,"Density %":88,"Assessment":155}
        tf,self._tree=_mktree(left,cols,widths,"Phrase"); tf.grid(row=1,column=0,sticky="nsew")
        for c in cols: self._tree.heading(c,text=c,command=lambda c=c:self._sort(c))
        self._tree.tag_configure("ok",   background=BG3,       foreground=SUCCESS)
        self._tree.tag_configure("warn", background="#181200", foreground=WARNING)
        self._tree.tag_configure("low",  background=BG4,       foreground=FG3)
        self._tree.tag_configure("focus",background="#00060F", foreground=ACCENT)
        rcm=tk.Menu(self,tearoff=0,bg=BG2,fg=FG,activebackground=ACCENT3,
                    activeforeground="#FFF",font=("Segoe UI",9))
        rcm.add_command(label="Copy Phrase",command=self._copy_sel)
        self._tree.bind("<Button-3>",lambda e:_popup(self,rcm,e))
        right=tk.Frame(content,bg=BG2); right.grid(row=0,column=1,sticky="nsew")
        right.rowconfigure(2,weight=1); right.columnconfigure(0,weight=1)
        fh=tk.Frame(right,bg=BG3); fh.grid(row=0,column=0,sticky="ew")
        tk.Label(fh,text="  FOCUS KEYWORD",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(side="left")
        fp=tk.Frame(right,bg=BG2); fp.grid(row=1,column=0,sticky="ew",padx=10,pady=10)
        self._focus_lbl=tk.Label(fp,text="",font=("Consolas",10),fg=FG2,bg=BG2,
                                 anchor="w",justify="left",wraplength=260)
        self._focus_lbl.pack(fill="x")
        ch=tk.Frame(right,bg=BG3); ch.grid(row=2,column=0,sticky="nsew")
        ch.rowconfigure(1,weight=1); ch.columnconfigure(0,weight=1)
        tk.Label(ch,text="  SERP COMPARISON",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(anchor="w")
        self._log=scrolledtext.ScrolledText(ch,font=("Consolas",8),bg=BG2,fg=FG2,
                                            relief="flat",highlightthickness=0,wrap="word",
                                            insertbackground=ACCENT,padx=8,pady=8,state="disabled")
        self._log.pack(fill="both",expand=True)
        self._bar=tk.Label(self,text="No analysis yet.",font=("Consolas",8),fg=FG3,bg=BG,anchor="w")
        self._bar.grid(row=3,column=0,sticky="ew",padx=10,pady=(2,4))

    def run(self):
        url=self._url.get().strip(); kw=self._kw.get().strip()
        if not url or url in ("https://","http://"): messagebox.showwarning("Input","Enter a URL."); return
        if not url.startswith("http"): url="https://"+url; self._url.delete(0,"end"); self._url.insert(0,url)
        do_compare=self._comp_flag.get(); sk=None
        if do_compare:
            sk=self._get_key()
            if not sk: return
        self._all_rows=[]; self._tree.delete(*self._tree.get_children())
        self._cnt_lbl.config(text=""); self._clear_log(); self._focus_lbl.config(text="")
        self._prog.grid(); self._prog.start(8)
        self._status.config(text="Fetching...",fg=ACCENT)
        self._bar.config(text=f"Fetching  {url}",fg=ACCENT)
        def worker():
            try:
                resp=requests.get(url,headers={"User-Agent":UA},timeout=TIMEOUT,allow_redirects=True)
                try:    soup=BeautifulSoup(resp.text,"lxml")
                except: soup=BeautifulSoup(resp.text,"html.parser")
                clean_text=_extract_body_text(soup)
                tokens=_tokenise(clean_text)
                total_words=len(tokens)
                raw_word_count=len(re.findall(r"\b\S+\b",clean_text))
            except Exception as ex:
                err=str(ex)
                self.after(0,lambda e=err:self._status.config(text=f"Error: {e}",fg=DANGER))
                self.after(0,lambda e=err:self._bar.config(text=f"Error: {e}",fg=DANGER))
                self.after(0,self._prog.stop); self.after(0,self._prog.grid_remove); return

            js_warning=""
            if raw_word_count < 100:
                js_warning="\n\nNote: Very few words detected.\nThis site may use JavaScript rendering.\nFor accurate results, try a static HTML page."

            all_rows=[]
            for n in (1,2,3): all_rows.extend(_calc_ngrams(tokens,n,top=40))
            focus_count,focus_density=0,0.0
            if kw:
                focus_count,focus_density=_kw_density_in_text(clean_text,kw)
                focus_row={"phrase":kw,"n":len(kw.split()),"count":focus_count,
                           "density":focus_density,"total":raw_word_count,"tag":"focus"}
                all_rows=[r for r in all_rows if r["phrase"].lower()!=kw.lower()]
                all_rows.insert(0,focus_row)
            self._all_rows=all_rows; self.after(0,self._populate)
            self.after(0,lambda:self._status.config(
                text=f"{total_words} content tokens  |  {raw_word_count} total words",fg=SUCCESS))
            self.after(0,lambda:self._bar.config(
                text=f"{url}  |  {total_words} tokens  |  {len(all_rows)} phrases",fg=SUCCESS))
            if kw:
                if 0.5<=focus_density<=2.5:
                    asses=f"Good density ({focus_density}%)"; col=SUCCESS
                elif focus_density>2.5:
                    asses=f"Over-optimised ({focus_density}%)"; col=DANGER
                else:
                    asses=f"Under-used ({focus_density}%)"; col=WARNING
                summary=(f"Keyword : {kw}\n"
                         f"Count   : {focus_count} times\n"
                         f"Density : {focus_density}%\n"
                         f"Total   : {raw_word_count} words\n\n{asses}"
                         f"{js_warning}")
                self.after(0,lambda s=summary,c=col:self._focus_lbl.config(text=s,fg=c))
            else:
                msg=f"No focus keyword set.{js_warning}" if js_warning else "No focus keyword set."
                self.after(0,lambda m=msg:self._focus_lbl.config(text=m,fg=WARNING if js_warning else FG3))
            if do_compare and sk and kw:
                self.after(0,lambda:self._log_w(f"SERP COMPARE : {kw}\n{'─'*44}"))
                self.after(0,lambda:self._status.config(text="Fetching competitors...",fg=ACCENT))
                try:
                    serp=_serper(kw,sk,gl="",hl="en",num=10); organic=serp.get("organic",[])[:10]
                    self.after(0,lambda n=len(organic):self._log_w(f"Found {n} URLs\n{'─'*44}"))
                    target_rank=None
                    for i,item in enumerate(organic,1):
                        if urlparse(item.get("link","")).netloc==urlparse(url).netloc: target_rank=i
                    rank_txt=f"Your page ranks #{target_rank}" if target_rank else "Your page NOT in top 10"
                    self.after(0,lambda t=rank_txt:self._log_w(f"{t}\n{'─'*44}"))
                    for i,item in enumerate(organic,1):
                        comp_url=item.get("link",""); comp_title=item.get("title","")[:55]
                        try:
                            cr=requests.get(comp_url,headers={"User-Agent":UA},timeout=15,allow_redirects=True)
                            try:    cs=BeautifulSoup(cr.text,"lxml")
                            except: cs=BeautifulSoup(cr.text,"html.parser")
                            ct=_extract_body_text(cs); cc,cd=_kw_density_in_text(ct,kw)
                            ctok=len(re.findall(r"\b\S+\b",ct))
                            icon="OK" if 0.5<=cd<=2.5 else ("HI" if cd>2.5 else "LO")
                            your=(" YOU "+str(focus_density)+"%" if urlparse(comp_url).netloc==urlparse(url).netloc else "")
                            line=f"#{i:02d} [{icon}] {cd:5.2f}%  ({cc}x/{ctok})  {comp_title}{your}"
                        except: line=f"#{i:02d} [ERR] (could not crawl)  {comp_title}"
                        self.after(0,lambda ln=line:self._log_w(ln))
                    self.after(0,lambda:self._log_w(f"\n{'─'*44}\nYOUR density : {focus_density}%\nIdeal range  : 0.5 - 2.5%"))
                except Exception as ex:
                    err=str(ex); self.after(0,lambda e=err:self._log_w(f"SERP error: {e}"))
            self.after(0,self._prog.stop); self.after(0,self._prog.grid_remove)
        threading.Thread(target=worker,daemon=True).start()

    def _populate(self,data=None):
        self._tree.delete(*self._tree.get_children())
        rows=data if data is not None else self._all_rows
        ng_filter=self._ngram_var.get(); tf=self._flt.get().lower(); filtered=[]
        for r in rows:
            if ng_filter!="All" and r["n"]!=int(ng_filter[0]): continue
            if tf and tf not in r["phrase"].lower(): continue
            filtered.append(r)
        for r in filtered:
            tag=r.get("tag","low")
            asses={"ok":"Good (0.5-2.5%)","warn":"High (>2.5%)",
                   "low":"Low (<0.5%)","focus":"Focus keyword"}.get(tag,"")
            self._tree.insert("","end",values=(r["phrase"],f"{r['n']}-gram",
                r["count"],f"{r['density']}%",asses),tags=(tag,))
        self._cnt_lbl.config(text=f"{len(filtered)} phrases")

    def _apply_filter(self): self._populate()

    def _sort(self,col):
        cm={"Phrase":"phrase","N-gram":"n","Count":"count","Density %":"density","Assessment":"tag"}
        self._sort_rev=not self._sort_rev
        self._all_rows.sort(key=lambda x:x.get(cm.get(col,"density"),0),reverse=self._sort_rev)
        self._apply_filter()

    def _clear(self):
        self._all_rows=[]; self._tree.delete(*self._tree.get_children()); self._clear_log()
        self._focus_lbl.config(text="",fg=FG2); self._cnt_lbl.config(text="")
        self._status.config(text="Cleared.",fg=FG3); self._bar.config(text="No analysis yet.",fg=FG3)

    def _copy_sel(self):
        sel=self._tree.selection()
        if sel: self.clipboard_clear(); self.clipboard_append(self._tree.item(sel[0],"values")[0])

    def _export(self):
        if not self._all_rows: messagebox.showinfo("No data","Run analysis first."); return
        p=filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV","*.csv")],initialfile="soliton_density.csv")
        if not p: return
        with open(p,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["phrase","n","count","density","total"])
            w.writeheader()
            w.writerows([{k:r[k] for k in ["phrase","n","count","density","total"]}
                         for r in self._all_rows])
        messagebox.showinfo("Exported",f"Saved:\n{p}")

    def _clear_log(self):
        self._log.configure(state="normal"); self._log.delete("1.0","end")
        self._log.configure(state="disabled")

    def _log_w(self,msg):
        self._log.configure(state="normal"); self._log.insert("end",msg+"\n")
        self._log.see("end"); self._log.configure(state="disabled")

    def get_state(self):
        return {"density_url":self._url.get().strip(),"density_kw":self._kw.get().strip()}

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL: SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════
class SchemaPanel(tk.Frame):
    def __init__(self,parent,cfg):
        super().__init__(parent,bg=BG); self._cfg=cfg; self._fields={}; self._build()

    def _build(self):
        self.columnconfigure(0,weight=1); self.rowconfigure(1,weight=1)
        cf=tk.Frame(self,bg=BG2); cf.grid(row=0,column=0,sticky="ew")
        ci=tk.Frame(cf,bg=BG2); ci.pack(fill="x",padx=14,pady=10); ci.columnconfigure(3,weight=1)
        tk.Label(ci,text="SCHEMA TYPE",font=("Consolas",9,"bold"),fg=FG2,bg=BG2).grid(row=0,column=0,padx=(0,8),sticky="w")
        self._type_var=tk.StringVar(value="Article")
        ttk.Combobox(ci,textvariable=self._type_var,values=SCHEMA_TYPES,width=22,state="readonly").grid(row=0,column=1,padx=(0,12))
        self._type_var.trace_add("write",lambda *_:self._reload_fields())
        _btn(ci,"GENERATE",self.generate,ACCENT2).grid(row=0,column=2,padx=(0,8))
        self._status=tk.Label(ci,text="Select schema type and fill in the fields.",
                              font=("Consolas",8),fg=FG3,bg=BG2,anchor="w")
        self._status.grid(row=0,column=3,sticky="ew",padx=(8,0))
        _btn(ci,"CLEAR",self._clear_fields,"#3A0A0A").grid(row=0,column=4,padx=(8,0))
        content=tk.Frame(self,bg=BG); content.grid(row=1,column=0,sticky="nsew")
        content.rowconfigure(0,weight=1); content.columnconfigure(0,weight=1); content.columnconfigure(1,weight=1)
        lf=tk.Frame(content,bg=BG); lf.grid(row=0,column=0,sticky="nsew",padx=(0,2))
        lf.rowconfigure(1,weight=1); lf.columnconfigure(0,weight=1)
        lh=tk.Frame(lf,bg=BG3); lh.grid(row=0,column=0,sticky="ew")
        tk.Label(lh,text="  FORM",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(side="left")
        tk.Label(lh,text="  * required",font=("Consolas",8),fg=WARNING,bg=BG3).pack(side="left")
        tk.Label(lh,text="No API",font=("Consolas",8),fg=SUCCESS,bg=BG3).pack(side="right",padx=10)
        self._cv=tk.Canvas(lf,bg=BG,highlightthickness=0,bd=0); self._cv.grid(row=1,column=0,sticky="nsew")
        vsb=ttk.Scrollbar(lf,orient="vertical",style="T.Vertical.TScrollbar",command=self._cv.yview)
        vsb.grid(row=1,column=1,sticky="ns"); self._cv.configure(yscrollcommand=vsb.set)
        self._form=tk.Frame(self._cv,bg=BG)
        self._win=self._cv.create_window((0,0),window=self._form,anchor="nw")
        self._form.bind("<Configure>",lambda _:self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.bind("<Configure>",lambda e:self._cv.itemconfig(self._win,width=e.width))
        self._cv.bind("<MouseWheel>",lambda e:self._cv.yview_scroll(-1*(e.delta//120),"units"))
        rf=tk.Frame(content,bg=BG2); rf.grid(row=0,column=1,sticky="nsew")
        rf.rowconfigure(1,weight=1); rf.columnconfigure(0,weight=1)
        rh=tk.Frame(rf,bg=BG3); rh.grid(row=0,column=0,sticky="ew")
        tk.Label(rh,text="  JSON-LD OUTPUT",font=("Consolas",9,"bold"),fg=ACCENT,bg=BG3,pady=7,padx=10).pack(side="left")
        br=tk.Frame(rh,bg=BG3); br.pack(side="right",padx=6,pady=4)
        _btn(br,"Copy",self._copy_output,BG3,small=True).pack(side="left",padx=(0,4))
        _btn(br,".html",self._export_html,"#054D36",small=True).pack(side="left",padx=(0,4))
        _btn(br,".json",self._export_json,"#054D36",small=True).pack(side="left")
        self._out=scrolledtext.ScrolledText(rf,font=("Consolas",9),bg="#000A14",fg="#00CCFF",
                                            relief="flat",highlightthickness=0,wrap="none",
                                            insertbackground=ACCENT,padx=10,pady=10,state="disabled")
        self._out.grid(row=1,column=0,sticky="nsew")
        for tag,col in [("key",ACCENT),("str","#88DDFF"),("brace",ACCENT2),
                        ("bool",WARNING),("num",SUCCESS),("tc","#005599")]:
            self._out.tag_configure(tag,foreground=col)
        self._vbar=tk.Label(self,text="",font=("Consolas",8),fg=FG3,bg=BG,anchor="w")
        self._vbar.grid(row=2,column=0,sticky="ew",padx=10,pady=(2,4))
        self._reload_fields()

    def _reload_fields(self):
        for w in self._form.winfo_children(): w.destroy()
        self._fields.clear(); self._cv.yview_moveto(0)
        stype=self._type_var.get(); fields=SCHEMA_FIELDS.get(stype,[])
        self._form.columnconfigure(0,weight=1)
        for i,(key,label,hint,multiline,required) in enumerate(fields):
            rf=tk.Frame(self._form,bg=BG); rf.grid(row=i,column=0,sticky="ew",padx=14,pady=(8,0))
            rf.columnconfigure(0,weight=1)
            tk.Label(rf,text=f"{'* ' if required else ''}{label}",
                     font=("Consolas",8,"bold" if required else "normal"),
                     fg=WARNING if required else FG2,bg=BG,anchor="w").grid(row=0,column=0,sticky="w")
            if multiline:
                w=tk.Text(rf,height=3,font=("Consolas",9),bg=BG3,fg=FG3,
                          insertbackground=ACCENT,relief="flat",bd=0,
                          highlightthickness=1,highlightbackground=BORDER,
                          highlightcolor=ACCENT,selectbackground=ACCENT3,
                          selectforeground="#FFFFFF",wrap="word",padx=6,pady=4)
                w.grid(row=1,column=0,sticky="ew",pady=(2,0))
                w.insert("1.0",hint)
                w.bind("<FocusIn>", lambda e,w=w,h=hint:self._ph_in(w,h))
                w.bind("<FocusOut>",lambda e,w=w,h=hint:self._ph_out(w,h))
            else:
                w=tk.Entry(rf,font=("Consolas",9),bg=BG3,fg=FG3,insertbackground=ACCENT,
                           relief="flat",bd=0,highlightthickness=1,
                           highlightbackground=BORDER,highlightcolor=ACCENT,
                           selectbackground=ACCENT3,selectforeground="#FFFFFF")
                w.grid(row=1,column=0,sticky="ew",pady=(2,0),ipady=5)
                w.insert(0,hint)
                w.bind("<FocusIn>", lambda e,w=w,h=hint:self._ph_in_e(w,h))
                w.bind("<FocusOut>",lambda e,w=w,h=hint:self._ph_out_e(w,h))
            self._fields[key]=(w,multiline,hint)
        tk.Frame(self._form,bg=BG,height=16).grid(row=len(fields),column=0)
        self._status.config(text=f"{stype}  {len(fields)} fields",fg=FG3); self._clear_output()

    def _ph_in(self,w,h):
        if w.get("1.0","end-1c")==h: w.delete("1.0","end"); w.config(fg=FG)
    def _ph_out(self,w,h):
        if not w.get("1.0","end-1c").strip(): w.delete("1.0","end"); w.insert("1.0",h); w.config(fg=FG3)
    def _ph_in_e(self,w,h):
        if w.get()==h: w.delete(0,"end"); w.config(fg=FG)
    def _ph_out_e(self,w,h):
        if not w.get().strip(): w.insert(0,h); w.config(fg=FG3)

    def _get_vals(self):
        vals={}; stype=self._type_var.get()
        for key,_,hint,multiline,_ in SCHEMA_FIELDS.get(stype,[]):
            entry=self._fields.get(key)
            if entry is None: continue
            w,is_ml,ph=entry
            if is_ml:
                raw=w.get("1.0","end-1c").strip(); vals[key]="" if raw==ph else raw
            else:
                raw=w.get().strip(); vals[key]="" if raw==ph else raw
        return vals

    def generate(self):
        stype=self._type_var.get(); vals=self._get_vals()
        fields=SCHEMA_FIELDS.get(stype,[])
        missing=[lbl for key,lbl,_,_,req in fields if req and not vals.get(key,"").strip()]
        if missing: self._status.config(text=f"Missing: {', '.join(missing[:3])}",fg=WARNING)
        try:
            ld=build_jsonld(stype,vals)
            wrapped='<script type="application/ld+json">\n'+json.dumps(ld,indent=2,ensure_ascii=False)+'\n</script>'
            self._write_output(wrapped)
            n_props=len([k for k in ld if k not in ("@context","@type")])
            if not missing: self._status.config(text=f"{stype}  generated  {n_props} properties",fg=SUCCESS)
            self._vbar.config(
                text="Some required fields are empty." if missing else "Paste the script block into your page head.",
                fg=WARNING if missing else FG3)
        except Exception as ex: self._status.config(text=f"Error: {ex}",fg=DANGER)

    def _write_output(self,text):
        self._out.configure(state="normal"); self._out.delete("1.0","end")
        self._out.insert("end",text); self._syntax_hl(); self._out.configure(state="disabled")

    def _syntax_hl(self):
        content=self._out.get("1.0","end")
        for tag in ("key","str","brace","bool","num","tc"): self._out.tag_remove(tag,"1.0","end")
        for pat,tg in [(r'<[^>]+>',"tc"),(r'"([^"]+)"\s*:',"key"),
                       (r':\s*"([^"]*)"',"str"),(r'\b(true|false|null)\b',"bool"),
                       (r':\s*(-?\d+\.?\d*)',"num"),(r'[{}\[\]]',"brace")]:
            for m in re.finditer(pat,content):
                self._out.tag_add(tg,f"1.0 + {m.start()} chars",f"1.0 + {m.end()} chars")

    def _clear_output(self):
        self._out.configure(state="normal"); self._out.delete("1.0","end")
        self._out.configure(state="disabled"); self._vbar.config(text="")

    def _get_out_text(self): return self._out.get("1.0","end-1c").strip()

    def _copy_output(self):
        txt=self._get_out_text()
        if not txt: messagebox.showinfo("Nothing","Generate a schema first."); return
        self.clipboard_clear(); self.clipboard_append(txt)
        self._status.config(text="Copied!",fg=SUCCESS)
        self.after(2000,lambda:self._status.config(text="Paste into your page head.",fg=FG3))

    def _export_html(self):
        txt=self._get_out_text()
        if not txt: messagebox.showinfo("Nothing","Generate a schema first."); return
        p=filedialog.asksaveasfilename(defaultextension=".html",filetypes=[("HTML","*.html")],
            initialfile=f"schema_{self._type_var.get().lower()}.html")
        if not p: return
        with open(p,"w",encoding="utf-8") as f: f.write(txt)
        messagebox.showinfo("Exported",f"Saved:\n{p}")

    def _export_json(self):
        txt=self._get_out_text()
        if not txt: messagebox.showinfo("Nothing","Generate a schema first."); return
        pure=re.sub(r'<[^>]+>',"",txt).strip()
        p=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")],
            initialfile=f"schema_{self._type_var.get().lower()}.json")
        if not p: return
        with open(p,"w",encoding="utf-8") as f: f.write(pure)
        messagebox.showinfo("Exported",f"Saved:\n{p}")

    def _clear_fields(self):
        for key,(w,is_ml,hint) in self._fields.items():
            if is_ml: w.delete("1.0","end"); w.insert("1.0",hint); w.config(fg=FG3)
            else: w.delete(0,"end"); w.insert(0,hint); w.config(fg=FG3)
        self._clear_output(); self._status.config(text="Cleared.",fg=FG3); self._vbar.config(text="")

    def get_state(self): return {}

# ═══════════════════════════════════════════════════════════════════════════════
# POPUP WINDOWS
# ═══════════════════════════════════════════════════════════════════════════════
class InfoWindow(tk.Toplevel):
    def __init__(self,master):
        super().__init__(master)
        self.title(f"About  SOLITONKIT  {VERSION}")
        W,H=620,320; sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.configure(bg=BG); self.resizable(False,False); self.grab_set(); _set_icon(self)
        self._build()

    def _build(self):
        outer=tk.Frame(self,bg=BORDER2); outer.pack(fill="both",expand=True,padx=1,pady=1)
        inner=tk.Frame(outer,bg=BG);    inner.pack(fill="both",expand=True)
        hdr=tk.Frame(inner,bg=HDRBG);   hdr.pack(fill="x")
        tk.Frame(hdr,bg=ACCENT,width=4).pack(side="left",fill="y")
        tk.Label(hdr,text=f"  ABOUT  SOLITONKIT  {VERSION}",
                 font=("Consolas",10,"bold"),fg=ACCENT,bg=HDRBG,pady=10,padx=6).pack(side="left")
        _hline(inner,BORDER).pack(fill="x")
        body=tk.Frame(inner,bg=BG); body.pack(fill="both",expand=True,padx=30,pady=16)
        lf=tk.Frame(body,bg=BG); lf.pack(fill="x",pady=(0,12))
        tk.Label(lf,text="SOLITON",font=("Consolas",20,"bold"),fg=ACCENT,bg=BG).pack(side="left")
        tk.Label(lf,text="KIT",    font=("Consolas",20,"bold"),fg=FG,   bg=BG).pack(side="left")
        tk.Label(lf,text=f"  {VERSION}",font=("Consolas",11,"bold"),fg=ACCENT3,bg=BG).pack(side="left",padx=(4,0))
        _hline(body,BORDER).pack(fill="x",pady=(0,14))
        gf=tk.Frame(body,bg=BG); gf.pack(fill="x"); gf.columnconfigure(1,weight=1)
        rows_data=[
            ("Created by :","Shak  (solidsman)",False,None),
            ("Email :","simplyabishak@gmail.com",True,"mailto:simplyabishak@gmail.com"),
            ("Version :",f"{VERSION} Final v2",False,None),
        ]
        for i,(label,value,clickable,url) in enumerate(rows_data):
            tk.Label(gf,text=label,font=("Consolas",9),fg=FG2,bg=BG,
                     anchor="w",width=14).grid(row=i,column=0,sticky="w",padx=(0,14),pady=5)
            if clickable and url:
                lk=tk.Label(gf,text=value,font=("Consolas",9,"underline"),fg=ACCENT,bg=BG,cursor="hand2",anchor="w")
                lk.grid(row=i,column=1,sticky="ew"); lk.bind("<Button-1>",lambda _,u=url:webbrowser.open(u))
            else:
                tk.Label(gf,text=value,font=("Consolas",9,"bold"),fg=FG,bg=BG,anchor="w").grid(row=i,column=1,sticky="ew")
        _hline(inner,BORDER).pack(fill="x")
        foot=tk.Frame(inner,bg=HDRBG); foot.pack(fill="x")
        _btn(foot,"Close",self.destroy,bg="#3A0A0A").pack(side="right",padx=16,pady=10)

class APIKeyWindow(tk.Toplevel):
    def __init__(self,master,cfg,on_save):
        super().__init__(master)
        self._cfg=cfg; self._on_save=on_save
        self.title(f"API Keys  SOLITONKIT  {VERSION}")
        W,H=700,330; sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.configure(bg=BG); self.resizable(True,False); self.minsize(560,300); self.grab_set(); _set_icon(self)
        self._build()

    def _build(self):
        outer=tk.Frame(self,bg=BORDER2); outer.pack(fill="both",expand=True,padx=1,pady=1)
        inner=tk.Frame(outer,bg=BG);    inner.pack(fill="both",expand=True)
        hdr=tk.Frame(inner,bg=HDRBG);   hdr.pack(fill="x")
        tk.Frame(hdr,bg=ACCENT,width=4).pack(side="left",fill="y")
        tk.Label(hdr,text="  API KEY CONFIGURATION",
                 font=("Consolas",11,"bold"),fg=ACCENT,bg=HDRBG,pady=12,padx=8).pack(side="left")
        tk.Label(hdr,text="Saved locally, never transmitted",
                 font=("Segoe UI",8),fg=FG3,bg=HDRBG).pack(side="right",padx=16)
        _hline(inner,BORDER).pack(fill="x")
        body=tk.Frame(inner,bg=BG); body.pack(fill="both",expand=True,padx=28,pady=14)
        body.columnconfigure(0,weight=1)
        def key_section(parent,row_i,icon,label,hint,link_txt,link_url,var_name):
            tk.Label(parent,text=f"{icon}  {label}",
                     font=("Consolas",9,"bold"),fg=ACCENT,bg=BG
                     ).grid(row=row_i,column=0,sticky="w",pady=(0,2))
            ef=tk.Frame(parent,bg=BG); ef.grid(row=row_i+1,column=0,sticky="ew",pady=(0,2))
            ef.columnconfigure(0,weight=1)
            e=_entry(ef,self._cfg.get(var_name,""),width=52)
            e.grid(row=0,column=0,sticky="ew",ipady=5,padx=(0,8))
            bf=tk.Frame(ef,bg=BG); bf.grid(row=0,column=1)
            _btn(bf,"Copy",  lambda e=e:self._copy(e),  BG3,small=True).pack(side="left",padx=(0,4))
            _btn(bf,"Paste", lambda e=e:self._paste(e), BG3,small=True).pack(side="left")
            hf=tk.Frame(parent,bg=BG); hf.grid(row=row_i+2,column=0,sticky="w",pady=(0,12))
            tk.Label(hf,text=hint,font=("Consolas",8),fg=FG3,bg=BG).pack(side="left")
            lk=tk.Label(hf,text=f"  {link_txt}",font=("Consolas",8,"underline"),
                        fg=ACCENT,bg=BG,cursor="hand2"); lk.pack(side="left")
            lk.bind("<Button-1>",lambda _,u=link_url:webbrowser.open(u)); return e
        self._e_serper=key_section(body,0,"S","SERPER.DEV  (Keywords + SERP Compare)",
            "Free 2,500 searches/month  ",
            "serper.dev","https://serper.dev","serper_api")
        self._e_ps=key_section(body,3,"G","GOOGLE PAGESPEED  (PageSpeed tab only)",
            "Free 25,000 requests/day  ",
            "console.cloud.google.com",
            "https://developers.google.com/speed/docs/insights/v5/get-started",
            "pagespeed_api")
        _hline(inner,BORDER).pack(fill="x")
        foot=tk.Frame(inner,bg=HDRBG); foot.pack(fill="x",padx=20,pady=10)
        self._msg=tk.Label(foot,text="",font=("Consolas",9),fg=FG3,bg=HDRBG,anchor="w")
        self._msg.pack(side="left",expand=True,fill="x")
        _btn(foot,"Close",    self.destroy,  bg="#3A0A0A").pack(side="right",padx=(8,0))
        _btn(foot,"Save Keys",self._save,    bg="#054D36").pack(side="right")

    def _copy(self,e):
        self.clipboard_clear(); self.clipboard_append(e.get())
        self._msg.config(text="Copied",fg=SUCCESS); self.after(2000,lambda:self._msg.config(text="",fg=FG3))

    def _paste(self,e):
        try:
            v=self.clipboard_get().strip(); e.delete(0,"end"); e.insert(0,v)
            self._msg.config(text="Pasted",fg=SUCCESS); self.after(1500,lambda:self._msg.config(text="",fg=FG3))
        except: pass

    def _save(self):
        self._cfg["serper_api"]=self._e_serper.get().strip()
        self._cfg["pagespeed_api"]=self._e_ps.get().strip()
        self._on_save(self._cfg); self._msg.config(text="Keys saved.",fg=SUCCESS); self.after(1200,self.destroy)

# ─── TOOL REGISTRY ────────────────────────────────────────────────────────────
TOOLS=[
    ("keywords","\u2315","KEYWORDS",   "Keyword Extractor"),
    ("crawler", "\u26cf","CRAWLER",    "On-Page SEO Audit"),
    ("pagespeed","\u26a1","PAGESPEED", "Core Web Vitals"),
    ("density", "\u2261","DENSITY",    "Keyword Density"),
    ("schema",  "\u27e8\u27e9","SCHEMA","JSON-LD Generator"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.C=cfg_load(); self._active_id="keywords"; self._panels={}; self._nav_items={}
        _apply_styles(self)
        self.title(APP_TITLE)
        # ── Responsive: start at 80% of screen, min 1100×680 ──
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        W = max(1100, min(1400, int(sw * 0.80)))
        H = max(680,  min(900,  int(sh * 0.85)))
        x = (sw - W) // 2
        y = max(0, (sh - H) // 2 - 20)
        self.geometry(f"{W}x{H}+{x}+{y}")
        self.minsize(1100,680)
        self.configure(bg=BG); self.resizable(True,True)
        _set_icon(self)
        self._build()
        self.protocol("WM_DELETE_WINDOW",self._quit)
        Splash(self,self._show_main)

    def _show_main(self):
        self.deiconify(); self.lift(); self.focus_force()

    def _build(self):
        self.rowconfigure(0,weight=1); self.columnconfigure(0,weight=1)
        root_pane=tk.Frame(self,bg=BG); root_pane.grid(row=0,column=0,sticky="nsew")
        root_pane.rowconfigure(0,weight=1); root_pane.columnconfigure(2,weight=1)

        # SIDEBAR
        sb=tk.Frame(root_pane,bg=SIDEBAR,width=190)
        sb.grid(row=0,column=0,sticky="nsew"); sb.grid_propagate(False)
        sb.columnconfigure(0,weight=1); sb.rowconfigure(99,weight=1)

        # Logo / wordmark
        logo_f=tk.Frame(sb,bg=SIDEBAR); logo_f.grid(row=0,column=0,sticky="ew")
        img=_load_logo(160,SIDEBAR); loaded=False
        if img:
            self._sb_logo=img
            tk.Label(logo_f,image=img,bg=SIDEBAR,pady=10).pack(); loaded=True
        if not loaded:
            wf=tk.Frame(logo_f,bg=SIDEBAR); wf.pack(pady=16)
            tk.Label(wf,text="SOLITON",font=("Consolas",11,"bold"),fg=ACCENT,bg=SIDEBAR).pack(side="left")
            tk.Label(wf,text="KIT",    font=("Consolas",11,"bold"),fg=FG,   bg=SIDEBAR).pack(side="left")

        tk.Label(sb,text=VERSION,font=("Consolas",8,"bold"),fg=ACCENT3,bg=SIDEBAR
                 ).grid(row=1,column=0,pady=(0,4))
        _hline(sb,BORDER).grid(row=2,column=0,sticky="ew")
        tk.Label(sb,text="  TOOLS",font=("Consolas",7,"bold"),fg=FG3,bg=SIDEBAR,anchor="w"
                 ).grid(row=3,column=0,sticky="ew",padx=4,pady=(8,2))

        for row_offset,(tid,icon,label,subtitle) in enumerate(TOOLS):
            self._nav_items[tid]=self._make_nav_item(sb,tid,icon,label,subtitle,row_offset+4)

        _hline(sb,BORDER).grid(row=99,column=0,sticky="sew")
        ftf=tk.Frame(sb,bg=SIDEBAR); ftf.grid(row=100,column=0,sticky="sew",padx=10,pady=(6,10))
        tk.Label(ftf,text="FREE  No API required",font=("Consolas",7,"bold"),
                 fg=SUCCESS,bg=SIDEBAR,anchor="w").pack(fill="x")
        tk.Label(ftf,text="Crawler  Density  Schema",font=("Consolas",7),
                 fg=FG3,bg=SIDEBAR,anchor="w").pack(fill="x")
        tk.Label(ftf,text="by  Solidsman  (Shak)",font=("Consolas",7),
                 fg=FG3,bg=SIDEBAR,anchor="w").pack(fill="x",pady=(4,0))
        self._serper_dot=tk.Label(ftf,text="",font=("Consolas",7),fg=FG3,bg=SIDEBAR,anchor="w")
        self._serper_dot.pack(fill="x",pady=(6,0))
        self._ps_dot=tk.Label(ftf,text="",font=("Consolas",7),fg=FG3,bg=SIDEBAR,anchor="w")
        self._ps_dot.pack(fill="x")
        bf=tk.Frame(ftf,bg=SIDEBAR); bf.pack(fill="x",pady=(8,0))
        _btn(bf,"API KEYS",self._open_api, bg=ACCENT3,small=True).pack(fill="x",pady=(0,4))
        _btn(bf,"INFO",    self._open_info,bg=BG3,    small=True).pack(fill="x")

        # Divider
        tk.Frame(root_pane,bg=BORDER,width=1).grid(row=0,column=1,sticky="ns")

        # Content area
        content_wrap=tk.Frame(root_pane,bg=BG); content_wrap.grid(row=0,column=2,sticky="nsew")
        content_wrap.rowconfigure(0,weight=1); content_wrap.columnconfigure(0,weight=1)
        self._panels["keywords"] =KeywordPanel(content_wrap,self._need_serper,self.C)
        self._panels["crawler"]  =CrawlerPanel(content_wrap,self.C)
        self._panels["pagespeed"]=PageSpeedPanel(content_wrap,self._need_ps,self.C)
        self._panels["density"]  =DensityPanel(content_wrap,self._need_serper,self.C)
        self._panels["schema"]   =SchemaPanel(content_wrap,self.C)
        for panel in self._panels.values():
            panel.grid(row=0,column=0,sticky="nsew"); panel.grid_remove()
        self._select("keywords"); self._refresh_indicators()

    def _make_nav_item(self,sb,tid,icon,label,subtitle,grid_row):
        outer=tk.Frame(sb,bg=SIDEBAR,cursor="hand2")
        outer.grid(row=grid_row,column=0,sticky="ew"); outer.columnconfigure(2,weight=1)
        stripe=tk.Frame(outer,bg=SIDEBAR,width=3); stripe.grid(row=0,column=0,rowspan=3,sticky="ns")
        icon_lbl=tk.Label(outer,text=icon,font=("Segoe UI Symbol",13),
                          fg=FG3,bg=SIDEBAR,width=3,pady=0)
        icon_lbl.grid(row=0,column=1,rowspan=3,sticky="w",padx=(4,2))
        tk.Frame(outer,bg=SIDEBAR,height=8).grid(row=0,column=2)
        name_lbl=tk.Label(outer,text=label,font=("Consolas",9,"bold"),fg=FG2,bg=SIDEBAR,anchor="w")
        name_lbl.grid(row=1,column=2,sticky="ew",padx=(0,8))
        sub_lbl=tk.Label(outer,text=subtitle,font=("Segoe UI",7),fg=FG3,bg=SIDEBAR,anchor="w")
        sub_lbl.grid(row=2,column=2,sticky="ew",padx=(0,8),pady=(0,8))
        all_w=[outer,stripe,icon_lbl,name_lbl,sub_lbl]
        def on_enter(_):
            if self._active_id!=tid:
                for w in all_w: w.configure(bg=SELHOV)
                stripe.configure(bg=ACCENT3)
        def on_leave(_):
            if self._active_id!=tid:
                for w in all_w: w.configure(bg=SIDEBAR)
                stripe.configure(bg=SIDEBAR)
        def on_click(_): self._select(tid)
        for w in all_w:
            w.bind("<Enter>",   on_enter)
            w.bind("<Leave>",   on_leave)
            w.bind("<Button-1>",on_click)
        return {"outer":outer,"stripe":stripe,"icon":icon_lbl,
                "name":name_lbl,"sub":sub_lbl,"all":all_w}

    def _select(self,tid):
        if self._active_id and self._active_id in self._nav_items:
            old=self._nav_items[self._active_id]
            for w in old["all"]: w.configure(bg=SIDEBAR)
            old["stripe"].configure(bg=SIDEBAR); old["icon"].configure(fg=FG3)
            old["name"].configure(fg=FG2); old["sub"].configure(fg=FG3)
        self._active_id=tid
        if tid in self._nav_items:
            new=self._nav_items[tid]
            for w in new["all"]: w.configure(bg=SELBG)
            new["stripe"].configure(bg=ACCENT); new["icon"].configure(fg=ACCENT)
            new["name"].configure(fg="#FFFFFF"); new["sub"].configure(fg=ACCENT)
        for pid,panel in self._panels.items():
            if pid==tid: panel.grid()
            else:        panel.grid_remove()

    def _refresh_indicators(self):
        sk=self.C.get("serper_api",""); pk=self.C.get("pagespeed_api","")
        self._serper_dot.config(text=f"Serper  {'SET' if sk else 'not set'}",fg=SUCCESS if sk else FG3)
        self._ps_dot.config(    text=f"PSI     {'SET' if pk else 'not set'}",fg=SUCCESS if pk else FG3)

    def _open_info(self): InfoWindow(self)

    def _open_api(self):
        def on_save(cfg):
            self.C.update(cfg); cfg_save(self.C); self._refresh_indicators()
        APIKeyWindow(self,self.C,on_save)

    def _need_serper(self):
        k=self.C.get("serper_api","").strip()
        if not k:
            messagebox.showerror("API Key Missing",
                "Click  API KEYS  in the sidebar and enter your Serper.dev key.\n\n"
                "Free 2,500 searches/month  serper.dev")
        return k

    def _need_ps(self):
        k=self.C.get("pagespeed_api","").strip()
        if not k:
            messagebox.showerror("API Key Missing",
                "Click  API KEYS  in the sidebar and enter your Google PageSpeed key.\n\n"
                "Free 25,000/day  console.cloud.google.com")
        return k

    def _quit(self):
        for pid in ("keywords","crawler","pagespeed","density","schema"):
            try: self.C.update(self._panels[pid].get_state())
            except: pass
        cfg_save(self.C); self.destroy()

# ─────────────────────────────────────────────────────────────────────────────
if __name__=="__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    App().mainloop()