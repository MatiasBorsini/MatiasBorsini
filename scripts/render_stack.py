#!/usr/bin/env python3
"""Generate the technology-stack SVGs for Matías Borsini's GitHub profile.

Visual inspiration: technology badges in Aahil Khan's profile README.
This is a tailored renderer and skill configuration, not a copy of the full
upstream profile generator. Requires: pip install fonttools
Run: python scripts/render_stack.py
"""
import base64, html, io, pathlib, urllib.request
from collections import defaultdict
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT, LOGOS, FONTS = ROOT / "assets", ROOT / "assets" / "tech-logos", ROOT / ".fonts"
FONT_URLS = {
    "SpaceGrotesk.ttf": "https://github.com/google/fonts/raw/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
    "SpaceMono-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/spacemono/SpaceMono-Regular.ttf",
}
THEMES = {
    "light": dict(paper="#F7F5EE", glow="rgba(255,255,255,0.8)", grid="rgba(22,22,22,0.07)", surface="#FFFFFF", ink="#161616", muted="rgba(22,22,22,0.62)", subtle="rgba(22,22,22,0.45)", accent="#FACC00", border="#161616"),
    "dark": dict(paper="#1A1B26", glow="rgba(192,202,245,0.05)", grid="rgba(192,202,245,0.07)", surface="#16161E", ink="#C0CAF5", muted="#A9B1D6", subtle="#949EC8", accent="#E0AF68", border="#C0CAF5"),
}
STACK = [
    ("Languages & Markup", [("C#", "csharp"), ("Java", "java"), ("JavaScript", "javascript"), ("TypeScript", "typescript"), ("HTML", "html5"), ("CSS", "css3"), ("XAML", None)]),
    ("Frameworks & Runtimes", [(".NET", "dotnet"), ("WPF", None), ("React", "react"), ("Next.js", "nextjs"), ("Node.js", "nodejs")]),
    ("Databases", [("SQL", None), ("SQLite", "sqlite"), ("PostgreSQL", "postgresql")]),
    ("Data & AI", [("Prisma", "prisma"), ("Supabase", "supabase"), ("Google Gemini", "gemini")]),
    ("Tools & Integrations", [("Git", "git"), ("GitHub", "github"), ("Telegram Bot API", "telegram")]),
    ("Testing", [("xUnit", None)]),
]
DARK_MARKS = {"nextjs", "github"}
NAP = [
    r"      |\      _,,,---,,_",
    r"      /,`.-'`'    -.  ;-;;,_",
    r"     |,4-  ) )-,_. ,\ (  `'-'",
    r"    '---''(_/--'  `-'\_)",
]
_static, _metrics = {}, {}
def font_file(name):
    path = FONTS / name
    if not path.exists():
        FONTS.mkdir(exist_ok=True)
        urllib.request.urlretrieve(FONT_URLS[name], path)
    return path
def static_font(face):
    if face not in _static:
        family, weight = face
        font = instancer.instantiateVariableFont(TTFont(font_file("SpaceGrotesk.ttf")), {"wght": weight}) if family == "G" else TTFont(font_file("SpaceMono-Regular.ttf"))
        buf = io.BytesIO(); font.save(buf); _static[face] = buf.getvalue()
    return _static[face]
def advance(face, value, size, spacing=0):
    if face not in _metrics:
        font = TTFont(io.BytesIO(static_font(face)))
        _metrics[face] = (font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm)
    cmap, hmtx, upm = _metrics[face]
    return sum(hmtx[cmap.get(ord(ch), ".notdef")][0] for ch in value) / upm * size + spacing * size * len(value)
def font_face(face, chars):
    font = TTFont(io.BytesIO(static_font(face))); opts = subset.Options()
    opts.flavor = "woff"; opts.layout_features = ["kern"]; opts.name_IDs = []
    sub = subset.Subsetter(opts); sub.populate(text="".join(sorted(chars))); sub.subset(font)
    buf = io.BytesIO(); font.save(buf); data = base64.b64encode(buf.getvalue()).decode()
    family = "G" if face[0] == "G" else "M"
    return f"@font-face{{font-family:{family};font-weight:{face[1]};src:url(data:font/woff;base64,{data}) format('woff')}}"
class Svg:
    def __init__(self, width, height, theme, title):
        self.width, self.height, self.theme, self.title = width, height, THEMES[theme], title
        self.parts, self.defs, self.rules, self.used = [], [], [], defaultdict(set)
    def text(self, x, y, value, size=14, weight=400, mono=False, fill="ink", spacing=0):
        face = ("M", 400) if mono else ("G", weight); self.used[face] |= set(value)
        spacing_attr = f' letter-spacing="{spacing}em"' if spacing else ""
        return f'<text x="{x:.2f}" y="{y:.2f}" font-family="{face[0]}" font-weight="{face[1]}" font-size="{size}" fill="{self.theme.get(fill, fill)}" xml:space="preserve"{spacing_attr}>{html.escape(value)}</text>'
    def paper(self, width, height):
        t = self.theme
        self.defs.extend([
            f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse" x="2" y="2"><path d="M40 0V40H0" fill="none" stroke="{t["grid"]}"/></pattern>',
            f'<radialGradient id="glow" cx="0.5" cy="0" r="0.8"><stop offset="0" stop-color="{t["glow"]}"/><stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>',
            f'<clipPath id="clip"><rect x="2" y="2" width="{width-10}" height="{height-10}" rx="14"/></clipPath>',
        ])
        self.parts.append(f'<rect x="8" y="8" width="{width-10}" height="{height-10}" rx="14" fill="{t["border"]}"/><rect x="2" y="2" width="{width-10}" height="{height-10}" rx="14" fill="{t["paper"]}" stroke="{t["border"]}" stroke-width="2"/><g clip-path="url(#clip)"><rect x="2" y="2" width="{width-10}" height="{height-10}" fill="url(#grid)"/><rect x="2" y="2" width="{width-10}" height="{height-10}" fill="url(#glow)"/></g>')
    def render(self):
        faces = "\n".join(font_face(face, chars) for face, chars in sorted(self.used.items()) if chars)
        css = "\n".join(self.rules)
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title"><title id="title">{html.escape(self.title)}</title><defs>{"".join(self.defs)}</defs><style>{faces}\n{css}\n@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>{"".join(self.parts)}</svg>'
def logo_uri(name):
    return "data:image/svg+xml;base64," + base64.b64encode((LOGOS / f"{name}.svg").read_bytes()).decode()
def render_stack(theme):
    width, row_h, top = 840, 48, 118
    height = top + len(STACK) * row_h + 44
    names = ", ".join(name for _, tools in STACK for name, _ in tools)
    c = Svg(width, height, theme, f"What I build with: {names}.")
    t = c.theme; c.paper(width, height)
    c.parts += [c.text(40, 54, "TOOLBOX", 11, 500, fill="muted", spacing=.16), c.text(40, 88, "What I build with", 28, 700, spacing=-.01)]
    if theme == "dark":
        c.defs.append('<filter id="invert-dark"><feColorMatrix type="matrix" values="0 0 0 0 0.753 0 0 0 0 0.792 0 0 0 0 0.961 0 0 0 1 0"/></filter>')
    c.rules.append("@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}")
    n = 0
    for r, (label, tools) in enumerate(STACK):
        y = top + r * row_h; c.parts.append(c.text(40, y + 19, label.upper(), 10.5, 500, fill="muted", spacing=.12))
        x = 196
        for name, logo in tools:
            tw = advance(("G", 500), name, 12.5)
            w = tw + (48 if logo else 26)
            if x + w > width - 10:
                raise ValueError(f"Badges overflow {label}: {name} ends at {x+w:.1f}")
            pieces = [f'<rect x="{x+3}" y="{y+3}" width="{w:.1f}" height="30" rx="8" fill="{t["border"]}"/>', f'<rect x="{x}" y="{y}" width="{w:.1f}" height="30" rx="8" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.8"/>']
            tx = x + 13
            if logo:
                filt = ' filter="url(#invert-dark)"' if theme == "dark" and logo in DARK_MARKS else ""
                pieces.append(f'<image x="{x+11}" y="{y+7}" width="16" height="16" href="{logo_uri(logo)}"{filt}/>')
                tx = x + 35
            pieces.append(c.text(tx, y + 19.5, name, 12.5, 500))
            c.parts.append(f'<g style="animation:pop .45s cubic-bezier(.16,1,.3,1) {0.15+n*.035:.3f}s both">{"".join(pieces)}</g>')
            n += 1; x += w + 10
    fs = 13; nx = width - 52 - .612 * fs * 29; ny = top + (len(STACK)-1) * row_h + 14
    for i, line in enumerate(NAP): c.parts.append(c.text(nx, ny+i*15, line, fs, mono=True, fill="muted"))
    c.rules.append("@keyframes zz{0%{opacity:0;transform:translate(0,0)}25%{opacity:1}100%{opacity:0;transform:translate(10px,-26px)}}")
    for j, size in enumerate((10, 12, 14)):
        c.parts.append(f'<g style="opacity:0;animation:zz 3.6s linear {j*1.2}s infinite">{c.text(nx+2+j*9, ny+12, "z", size, mono=True, fill="subtle")}</g>')
    return c.render()
if __name__ == "__main__":
    for theme in THEMES:
        (OUT / f"stack-{theme}.svg").write_text(render_stack(theme), encoding="utf-8")
