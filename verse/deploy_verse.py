#!/usr/bin/env python3
# Publish the built pages to their own address, kat-titter.github.io/vanitas_veritas_verse/: iii as index.html, with veritas
# (sync.html), the doc for vanitas (sink.html), the black paper and the pitch beside it, and macroverse.html, which iii links
# to. Links between them are rewritten for the new home; i and ii stay at the project's address,
# kat-titter.github.io/vanitas-veritas/verse/. The sources and the build stay here; only built pages go there.
#   python3 verse/deploy_verse.py                 every page as it is on disk
#   python3 verse/deploy_verse.py --committed     every page as last committed here (while the working tree is being edited;
#                                                 it reads HEAD:verse/, so it works only once the move to verse/ is committed)
# The link preview (og.jpg, 1200x630, about 60 KB: an image from iii on ink) lives only in the published repo, never here
# (no binaries in the source repo); the meta tags that point at it are added at publish time.
#   python3 verse/deploy_verse.py --no-macroverse leave macroverse.html out (while it is being rebuilt)
#   add --push to commit and push (otherwise it only writes the files)
import pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
DEST = pathlib.Path.home() / 'Claude/Projects/vanitas_veritas_verse'
OLD = 'https://kat-titter.github.io/vanitas-veritas/verse/'
args = set(sys.argv[1:])

def read(name, committed=False):
    if committed:
        return subprocess.run(['git', 'show', f'HEAD:verse/{name}'], cwd=HERE, capture_output=True, text=True, check=True).stdout
    return (HERE / name).read_text()

def rehome(html):
    html = re.sub(r'(href|src)="veritas3\.html', r'\1="./', html)                  # iii is the home page there
    html = re.sub(r"(['\"])veritas3\.html", r"\1./", html)                           # the same, inside scripts
    html = re.sub(r'href="(veritas2?\.html)', lambda m: f'href="{OLD}{m.group(1)}', html)   # i and ii stay where they were
    return html

C = '--committed' in args
pages = {'index.html': read('veritas3.html', C), 'blackpaper.html': read('blackpaper.html', C), 'pitch.html': read('pitch.html', C)}
if '--no-macroverse' not in args and (HERE / 'macroverse.html').exists():
    pages['macroverse.html'] = read('macroverse.html', C)
if (HERE / 'sink.html').exists(): pages['sink.html'] = read('sink.html', C)     # vanitas, the sink, redesigned
if (HERE / 'sync.html').exists(): pages['sync.html'] = read('sync.html', C)     # veritas: one water with vanitas

NEW = 'https://kat-titter.github.io/vanitas_veritas_verse/'
def preview(html, name):                      # the picture a shared link unfurls with, on every page
    url = NEW + ('' if name == 'index.html' else name)
    tags = (f'<meta property="og:url" content="{url}">\n<meta property="og:image" content="{NEW}og.jpg">\n'
            '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            f'<meta name="twitter:image" content="{NEW}og.jpg">\n')
    html = re.sub(r'<meta name="twitter:card" content="[^"]*">\n?', '', html)
    if 'property="og:title"' not in html:
        title = re.search(r'<title>(.*?)</title>', html)
        desc = re.search(r'<meta name="description" content="([^"]*)">', html)
        tags = (f'<meta property="og:title" content="{title.group(1) if title else "vanitas_veritas"}">\n'
                + (f'<meta property="og:description" content="{desc.group(1)}">\n' if desc else '') + '<meta property="og:type" content="website">\n' + tags)
    tags += '<meta name="twitter:card" content="summary_large_image">\n'
    return html.replace('<meta charset="utf-8">\n', '<meta charset="utf-8">\n' + tags, 1)

for name, html in pages.items():
    (DEST / name).write_text(preview(rehome(html) if name != 'index.html' else html, name))
(DEST / '.nojekyll').write_text('')
(DEST / 'README.md').write_text("""# vanitas_veritas

A sink you cannot wash your hands in. The water is a machine dreaming: reach in, and it slips away. No water, no dream.
It stands in two places with one water: vanitas, the sink, proposed, and veritas, the same basin on the web.

- veritas: https://kat-titter.github.io/vanitas_veritas_verse/sync.html
- vanitas (proposed): https://kat-titter.github.io/vanitas_veritas_verse/sink.html
- the black paper: https://kat-titter.github.io/vanitas_veritas_verse/blackpaper.html
- the earlier web piece, iii: https://kat-titter.github.io/vanitas_veritas_verse/

By Kat Titterton (macrofluidic). These are built pages; the sources live in https://github.com/kat-titter/vanitas-veritas.
""")
print('wrote', ', '.join(sorted(pages)), 'to', DEST)
if '--push' in args:
    subprocess.run(['git', 'add', '-A'], cwd=DEST, check=True)
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=DEST).returncode:
        subprocess.run(['git', 'commit', '-q', '-m', 'publish the piece\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'], cwd=DEST, check=True)
        subprocess.run(['git', 'push', '-q', '-u', 'origin', 'HEAD:main'], cwd=DEST, check=True)
        print('pushed')
    else:
        print('nothing changed')
