#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, re, codecs, htmlmin, cssmin, time, colorsys, urlparse
from scss import parser
from bs4 import BeautifulSoup

PALETTES_DIRECTORY  =   "sass/palettes"
NAMES               =   {
    "ios7":     "iOS 7",
    "flatui":   "Flat UI",
    "goldfish": "Giant Goldfish",
}
URIS                =   {
    "ios7":     "http://ios7colors.com/",
    "flatui":   "http://flatuicolors.com/",
    "goldfish": "http://www.colourlovers.com/palette/92095/Giant_Goldfish"
}

def camel_to_hyphen(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()

def normalize_hex(hex_):
    hex_ = hex_.lstrip("#")   # in case you have Web color specs
    if len(hex_) == 3:
        hex_  =   "%s%s%s%s%s%s" % (hex_[0:1], hex_[0:1], hex_[1:2], hex_[1:2], hex_[2:3], hex_[2:3])
    return hex_

def get_rgb(hexrgb):
    hexrgb  = normalize_hex(hexrgb)
    r, g, b = (int(hexrgb[i:i+2], 16) / 255.0 for i in xrange(0,5,2))
    return (r, g, b)

def get_hsl(hexrgb):
    hexrgb  = normalize_hex(hexrgb)
    r, g, b = (int(hexrgb[i:i+2], 16) / 255.0 for i in xrange(0,5,2))
    return colorsys.rgb_to_hls(r, g, b)

def nice_uri(uri):
    uri     =   urlparse.urlparse(uri)
    return uri.netloc.split(":")[0].lstrip("www.") + ("&hellip;" if not uri.path == "/" else "")

index       =   codecs.open("index.tmpl.html", "r", "utf-8")
markup      =   BeautifulSoup(index.read(), "html5lib")
index.close()

assert not markup.main == None, "<main> is not found"
assert not markup.style == None, "<style> is not found"

if markup.find(id = "palettes"):
    palettes    =   markup.find(id = "palettes")
    palettes.clear()
else:
    palettes        =   markup.new_tag("ul", id = "palettes")
    markup.main.append(palettes)
if markup.find(id = "primary-nav"):
    nav             =   markup.find(id = "primary-nav")
    nav.clear()
else:
    nav             =   markup.new_tag("nav", id = "primary-nav")
    markup.header.append(nav)
nav_ul          =   markup.new_tag("ul")
nav.append(nav_ul)

palettes_css    =   []
palettes_markup =   {}

if markup.find(id = "swatch-css"):
    style           =   markup.find(id = "swatch-css")
    style.clear()
else:
    style           =   markup.new_tag("style", id = "swatch-css")

for f in os.listdir(PALETTES_DIRECTORY):
    if f.endswith(".scss"):
        name    =   os.path.splitext(f)[0]
        palettes_markup[name]   =   []
        palette =   palettes_markup[name]
        f       =   open(os.path.join(PALETTES_DIRECTORY, f), "r")
        css     =   parser.Stylesheet(options = {"compress": False})
        css.loads(f.read())
        colors  =   css.ctx
        f.close()
        for color in colors:
            palettes_css.append(".swatch-%s-%s{background-color: %s}" % (name, camel_to_hyphen(color), colors.get(color)))
            palette.append({
                "name": color,
                "hex":  str(colors[color]),
                "rgb":  get_rgb(str(colors[color])),
                "hsl":  get_hsl(str(colors[color])),
            })

style.append(cssmin.cssmin("".join(palettes_css)))
markup.style.insert_after("\n")
markup.style.insert_after(style)
markup.style.string =   cssmin.cssmin(markup.style.string)
nav_tab_index   =   1
li_tab_index    =   1

keys    =   palettes_markup.keys()
keys.sort()

for palette in keys:
    name        =   NAMES[palette]
    slug        =   palette
    palette     =   sorted(palettes_markup[palette], key = lambda x: x.get("hsl"))
    group_li    =   markup.new_tag("li", **{"id": slug, "class": "palette"})
    h2          =   markup.new_tag("h2")
    h2.string   =   name
    p_import    =   markup.new_tag("p", **{"class": "import"})
    p_import.string  =   "@import \"palettes/%s\";" % slug
    group_ul    =   markup.new_tag("ul")
    group_li.append(h2)
    group_li.append(p_import)
    if slug in URIS:
        p_uri   =   markup.new_tag("p", **{"class": "uri"})
        a_uri   =   markup.new_tag("a", href = URIS[slug], title = nice_uri(URIS[slug]), target = "_blank")
        a_uri.string    =   nice_uri(URIS[slug])
        p_uri.append(a_uri)
        group_li.append(p_uri)
    nav_li      =   markup.new_tag("li")
    nav_a       =   markup.new_tag("a", href = "#%s" % slug, title = "Go to %s" % name, tabindex = nav_tab_index)
    nav_a.string=   name
    nav_li.append(nav_a)
    nav_ul.append(nav_li)
    nav_tab_index   +=  1
    for color in palette:
        li                  =   markup.new_tag("li", **{"id": "%s-%s" % (slug, camel_to_hyphen(color.get("name"))), "tabindex": len(palettes_markup.keys()) + li_tab_index, "class": "color"})
        span_swatch         =   markup.new_tag("span", **{"class": "swatch-%s-%s swatch" % (slug, camel_to_hyphen(color.get("name")))})
        span_name           =   markup.new_tag("span", **{"class": "name"})
        span_name.string    =   markup.new_string("$%s" % color.get("name"))
        input_hex           =   markup.new_tag("input", **{"class": "hex", "type": "text", "value": "#%s" % normalize_hex(color.get("hex")), "spellcheck": "false"})
        input_rgb           =   markup.new_tag("input", **{"class": "rgb", "type": "text", "value": "rgb(%d,%d,%d)" % (color.get("rgb")[0] * 100, color.get("rgb")[1] * 100, color.get("rgb")[2] * 100), "spellcheck": "false"})
        input_hsl           =   markup.new_tag("input", **{"class": "hsl", "type": "text", "value": "hsl(%d,%d,%d)" % (color.get("hsl")[0] * 100, color.get("hsl")[1] * 100, color.get("hsl")[2] * 100), "spellcheck": "false"})
        li.append(span_swatch)
        li.append(span_name)
        li.append(input_hex)
        # li.append(input_rgb)
        # li.append(input_hsl)
        group_ul.append(li)
        li_tab_index        +=  1
    group_li.append(group_ul)
    palettes.append(group_li)
index       =   codecs.open("index.html", "w", "utf-8")
index.write(unicode(markup))
index.flush()
index.close()
