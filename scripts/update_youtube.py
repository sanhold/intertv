#!/usr/bin/env python3
"""Synchronise le site avec la chaîne YouTube INTER TV CI.

Lit le flux public de la chaîne, puis régénère les blocs délimités par
<!-- yt:NOM:start --> ... <!-- yt:NOM:end --> dans les pages HTML.
Sans dépendance externe (bibliothèque standard uniquement).
"""
import datetime
import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANNEL_ID = 'UCBNY9EYKA9dHCqyjfpqP8xg'
CHANNEL_URL = 'https://www.youtube.com/@intertvci'
FEED_URL = f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']

NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015',
      'm': 'http://search.yahoo.com/mrss/'}


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'fr-FR,fr;q=0.9', **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', errors='replace')


def load_videos():
    root = ET.fromstring(fetch(FEED_URL))
    videos = []
    for e in root.findall('a:entry', NS):
        d = datetime.date.fromisoformat(e.findtext('a:published', namespaces=NS)[:10])
        stats = e.find('m:group/m:community/m:statistics', NS)
        videos.append({
            'id': e.findtext('yt:videoId', namespaces=NS),
            'title': e.findtext('a:title', namespaces=NS).strip(),
            'date': f'{d.day} {MOIS[d.month - 1]} {d.year}',
            'views': int(stats.get('views')) if stats is not None else 0,
        })
    return videos


def load_stats():
    """Abonnés et nombre de vidéos, lus sur la page de la chaîne (None si illisible)."""
    try:
        page = fetch(CHANNEL_URL + '/videos', {'Cookie': 'CONSENT=YES+1; SOCS=CAI'})
    except Exception as exc:  # le site doit continuer à se mettre à jour sans les stats
        print('Stats indisponibles :', exc)
        return None, None
    subs = re.search(r'"content":"([\d.,\s  KMk]+?)[\s  ]*(?:abonn|subscriber)', page)
    vids = re.search(r'"content":"(\d[\d\s  .,]*)[\s  ]*(?:vid[ée]o)', page)
    clean = lambda m: re.sub(r'[\s  ]+', ' ', m.group(1)).strip() if m else None
    return clean(subs), clean(vids)


def classify(title):
    """Renvoie (catégorie de filtre, libellé) d'après le titre."""
    t = title.lower()
    if 'flash info' in t:
        return 'flash', 'Flash Info'
    if re.match(r'actu\b', t):
        return 'flash', 'Actu'
    if 'direct' in t:
        return 'direct', 'Direct'
    if re.search(r'concert|musique|clip|festival|culture', t):
        return 'culture', 'Culture · Concert'
    if re.search(r'débat|\bia\b|l\'ia|emploi|intelligence artificielle|économi(?!e verte)', t):
        return 'debat', 'Débat · Économie'
    if re.search(r'environnement|salubrité', t):
        return 'societe', 'Environnement'
    if re.search(r'santé|nutrition', t):
        return 'societe', 'Santé'
    if re.search(r'chef|chefferie', t):
        return 'societe', 'Société · Chefferie'
    return 'societe', 'Société'


def fmt_views(n):
    if n == 0:
        return 'Nouveau'
    return f'{n:,} vue{"s" if n > 1 else ""}'.replace(',', ' ')


def card(v, filtered):
    cat, label = classify(v['title'])
    title = html.escape(v['title'])
    attr = f' data-category="{cat}"' if filtered else ''
    return f'''        <a class="card video-card" href="https://www.youtube.com/watch?v={v['id']}" target="_blank" rel="noopener"{attr}>
          <div class="card-media"><img src="https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg" alt="{title}" loading="lazy"><span class="play-overlay"><i class="fa-solid fa-play"></i></span><span class="badge badge--yt"><i class="fa-brands fa-youtube"></i> YouTube</span></div>
          <div class="card-body">
            <div class="card-cat">{label}</div>
            <h3>{title}</h3>
            <div class="card-meta"><span>{v['date']}</span><span>{fmt_views(v['views'])}</span></div>
          </div>
        </a>
'''


def grid(videos, filtered=False):
    return '<div class="grid grid--3">\n' + ''.join(card(v, filtered) for v in videos) + '      </div>'


def replace_block(text, name, content):
    pattern = re.compile(rf'(<!-- yt:{name}:start -->).*?(<!-- yt:{name}:end -->)', re.S)
    if not pattern.search(text):
        raise SystemExit(f'Marqueur yt:{name} introuvable')
    return pattern.sub(lambda m: f'{m.group(1)}\n      {content}\n      {m.group(2)}', text)


def update(path, name, content):
    f = ROOT / path
    old = f.read_text(encoding='utf-8')
    new = replace_block(old, name, content)
    if new != old:
        f.write_text(new, encoding='utf-8', newline='\n')
        print('Mis à jour :', path)


def main():
    videos = load_videos()
    if not videos:
        sys.exit('Aucune vidéo reçue : on ne touche à rien.')
    lives = [v for v in videos if classify(v['title'])[0] == 'direct']
    replays = (lives + [v for v in videos if v not in lives])[:3]

    update('index.html', 'home', grid(videos[:3]))
    update('actualites.html', 'all', grid(videos, filtered=True))
    update('programmes.html', 'latest', grid(videos[:6]))
    update('direct.html', 'replays', grid(replays))

    subs, vids = load_stats()
    if subs and vids:
        update('index.html', 'stats',
               f'<div class="yt-stats"><div><strong>{subs}</strong><span>abonnés</span></div>'
               f'<div><strong>{vids}</strong><span>vidéos</span></div>'
               f'<div><strong>@intertvci</strong><span>notre chaîne</span></div></div>')
    print(f'{len(videos)} vidéos, abonnés={subs}, vidéos={vids}')


if __name__ == '__main__':
    main()
