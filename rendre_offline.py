#!/usr/bin/env python3
"""Rend Moteur-Sorento-2014-3D.html 100 % hors ligne (un seul fichier).
Usage : python3 rendre_offline.py Moteur-Sorento-2014-3D.html
Crée Moteur-Sorento-2014-3D-offline.html dans le même dossier.
Rien d'autre n'est modifié dans la page."""
import base64, re, sys, os, urllib.request

SRC = sys.argv[1] if len(sys.argv) > 1 else "Moteur-Sorento-2014-3D.html"
OUT = os.path.join(os.path.dirname(os.path.abspath(SRC)), "Moteur-Sorento-2014-3D-offline.html")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
BASE = "https://cdn.jsdelivr.net/npm/three@0.147.0/"
JS = ["build/three.min.js",
      "examples/js/controls/OrbitControls.js",
      "examples/js/environments/RoomEnvironment.js"]
FONTS = "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600&display=swap"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

html = open(SRC, encoding="utf-8").read()

# 1-2. Three.js 0.147.0 intégré, même ordre
for path in JS:
    url = BASE + path
    tag = f'<script src="{url}"></script>'
    if tag not in html:
        sys.exit(f"Balise introuvable : {tag}")
    code = get(url).decode("utf-8")
    code = code.replace("</script", "<\\/script")  # sécurité dans une balise inline
    # Retire les adresses web présentes uniquement dans les commentaires du code
    code = "\n".join(re.sub(r"https?://\S+", "", l) if l.lstrip().startswith(("//", "/*", "*")) else l
                     for l in code.split("\n"))
    # ... et celles des simples messages d'avertissement (on garde les espaces de noms w3.org, indispensables)
    code = re.sub(r"https?://(?!www\.w3\.org/)[^\s\"'`)]+", "", code)
    print(f"OK  {path}  ({len(code)//1024} Ko)")
    html = html.replace(tag, f"<script>/* three@0.147.0 {path} */\n{code}\n</script>", 1)

# 3. Polices Google en base64
link_pre = '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
link_css = f'<link href="{FONTS}" rel="stylesheet">\n'
try:
    css = get(FONTS).decode("utf-8")
    def inline(m):
        data = base64.b64encode(get(m.group(1))).decode()
        return f"url(data:font/woff2;base64,{data}) format('woff2')"
    css = re.sub(r"url\((https://[^)]+\.woff2)\)\s*format\('woff2'\)", inline, css)
    html = html.replace(link_pre, "").replace(link_css, f"<style>/* Barlow + Barlow Condensed (Google Fonts, OFL) */\n{css}</style>\n")
    print("OK  polices Barlow intégrées en base64")
except Exception as e:
    html = html.replace(link_pre, "").replace(link_css, "")
    print(f"!!  polices non téléchargées ({e}) : lien supprimé, polices système utilisées")

# 4. Vérification des liens externes
reste = sorted(set(re.findall(r"https?://[^\s\"'`)<>]+", html)))
externes = [u for u in reste if not u.startswith("http://www.w3.org/")]
print("Liens externes restants :", externes or "aucun")
if any(u.startswith("http://www.w3.org/") for u in reste):
    print("(Les adresses w3.org restantes sont des espaces de noms internes de Three.js, rien n'est chargé depuis Internet.)")

open(OUT, "w", encoding="utf-8").write(html)
print(f"Fichier créé : {OUT}  ({os.path.getsize(OUT)//1024} Ko)")
