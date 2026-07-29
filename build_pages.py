"""Generate SEO artifacts from catalog.js: static product pages, sitemap.xml,
and the Google Merchant Center feed.

Runs after sync_catalog.py (reads catalog.js, no network calls). Emits:
  products/<handle>.html  — fully prerendered product pages (crawlable without JS;
                            pdp.js hydrates them for interactivity)
  sitemap.xml             — all indexable pages
  merchant-feed.xml       — Google Merchant feed, AD-ELIGIBLE PRODUCTS ONLY
                            (weapon SKUs excluded per Google Shopping policy)

    python build_pages.py
"""
import datetime
import html as html_mod
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://melisdefenseboutique.com"
PRODUCTS_DIR = os.path.join(ROOT, "products")

# Google Shopping prohibits weapons (pepper spray, knives, kubatons/batons).
# Products whose text or variant options match these terms stay out of the feed.
FEED_BLOCK_TERMS = ("pepper spray", "knife", "knives", "kubaton", "knuckle", "blade", "stun")


def esc(s):
    return html_mod.escape(s, quote=True)


def load_catalog():
    raw = open(os.path.join(ROOT, "catalog.js"), encoding="utf-8").read()
    return json.loads(raw[raw.index("["):raw.index("];") + 1])


def product_text(p):
    opts = " ".join(v for o in p["options"] for v in o["values"])
    return (p["title"] + " " + " ".join(p["desc"]) + " " + opts).lower()


def feed_eligible(p):
    return not any(t in product_text(p) for t in FEED_BLOCK_TERMS)


def page_url(p):
    return "%s/products/%s.html" % (BASE, p["handle"])


def img_url(p, i=0):
    src = p["images"][i] if p["images"] else ""
    return src if src.startswith("http") else "%s/%s" % (BASE, src)


CHROME_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Figtree:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<meta property="og:site_name" content="Meli's Defense Boutique">
<meta property="og:type" content="product">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<script async src="https://www.googletagmanager.com/gtag/js?id=GT-K822CJJZ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','GT-K822CJJZ');</script>
<script type="application/ld+json">{jsonld}</script>
</head>
<body data-handle="{handle}">

<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>
    <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><line x1="16.5" y1="16.5" x2="21" y2="21"/></symbol>
    <symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 5-6 8-6s6.5 2 8 6"/></symbol>
    <symbol id="i-bag" viewBox="0 0 24 24"><path d="M6 8h12l1 13H5L6 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></symbol>
  </defs>
</svg>

<div class="announce" aria-label="Store announcements">
  <div class="track">
    <span>FREE US SHIPPING OVER <span class="volt">$100</span></span>
    <span class="pinky">&#9733;</span>
    <span>VETERAN WOMAN OWNED &amp; OPERATED</span>
    <span class="pinky">&#9733;</span>
    <span>PACKED BY MELISSA &mdash; SHIPS IN 5&ndash;7 BUSINESS DAYS</span>
    <span class="pinky">&#9733;</span>
    <span>HAND-PICKED TOOLS &mdash; <span class="volt">SHE'S GOT YOUR SIX</span></span>
    <span class="pinky">&#9733;</span>
    <span>FREE US SHIPPING OVER <span class="volt">$100</span></span>
    <span class="pinky">&#9733;</span>
    <span>VETERAN WOMAN OWNED &amp; OPERATED</span>
    <span class="pinky">&#9733;</span>
    <span>THANK YOU FOR SUPPORTING <span class="volt">MY SMALL BUSINESS</span></span>
  </div>
</div>

<header class="site">
  <div class="wrap masthead">
    <a class="logo" href="/index.html">MELI'S<span class="tick">&#9733;</span>DEFENSE<small>BOUTIQUE &middot; EST. 2021</small></a>
    <nav class="main" aria-label="Main navigation">
      <a class="hot" href="/shop.html">Shop All</a>
      <a href="/shop.html#self-defense">Self-Defense</a>
      <a href="/shop.html#kids">Kids</a>
      <a href="/shop.html#add-ons">Add-Ons</a>
      <a href="/shop.html#accessories">Accessories</a>
      <a href="/index.html#melissa">Meet Melissa</a>
    </nav>
    <div class="head-icons">
      <a href="/shop.html" aria-label="Search"><svg><use href="#i-search"/></svg></a>
      <a href="https://melis-defense-boutique.myshopify.com/account" aria-label="Account"><svg><use href="#i-user"/></svg></a>
      <a href="#" class="cart-open" aria-label="Cart, 0 items"><svg><use href="#i-bag"/></svg> <span class="cart-count">(0)</span></a>
    </div>
  </div>
</header>
"""

CHROME_FOOT = """
<footer class="site">
  <div class="wrap foot-grid">
    <div>
      <h4>Meli's Defense Boutique</h4>
      <p>Cute, carry-anywhere safety gear, hand-packed by a U.S. veteran in Virginia. Every woman deserves to feel safe and empowered.</p>
    </div>
    <div>
      <h4>Shop</h4>
      <a href="/shop.html#self-defense">Self-Defense Keychains</a>
      <a href="/shop.html#kids">Kid Friendly</a>
      <a href="/shop.html#add-ons">Add-Ons</a>
      <a href="/shop.html#accessories">Accessories</a>
      <a href="/products/gift-card.html">Gift Cards</a>
    </div>
    <div>
      <h4>Help</h4>
      <a href="mailto:melisdefenseboutique@gmail.com">Contact Melissa</a>
      <a href="/index.html#melissa">Meet the Maker</a>
      <a href="/are-self-defense-keychains-legal.html">Are They Legal?</a>
      <a href="https://melis-defense-boutique.myshopify.com/account">Your Account</a>
    </div>
    <div>
      <h4>The Fine Print</h4>
      <a href="/policies.html#privacy">Privacy Policy</a>
      <a href="/policies.html#terms">Terms of Service</a>
      <a href="/policies.html#refunds">Refund Policy</a>
      <a href="/policies.html#shipping">Shipping Policy</a>
      <a href="/policies.html#restrictions">Shipping Restrictions</a>
    </div>
  </div>
  <div class="wrap foot-legal">
    <span>&copy; 2026 Meli's Defense Boutique &middot; Virginia, USA</span>
    <span>Some products have state shipping restrictions and are sold to adults 18+ only. Know your local laws.</span>
  </div>
</footer>

<div class="sticky-atc">
  <div><b id="sticky-title"></b><br><span style="font-size:12px;" id="sticky-price"></span></div>
  <button class="btn btn-pink" id="sticky-atc-btn">Add to cart</button>
</div>

<script src="/catalog.js"></script>
<script src="/render.js"></script>
<script src="/cart.js"></script>
<script src="/pdp.js"></script>

</body>
</html>
"""


def jsonld_for(p):
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["title"],
        "description": " ".join(p["desc"])[:5000],
        "image": [img_url(p, i) for i in range(len(p["images"]))][:10],
        "url": page_url(p),
        "brand": {"@type": "Brand", "name": "Meli's Defense Boutique"},
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "USD",
            "lowPrice": "%.2f" % p["price"],
            "highPrice": "%.2f" % p["priceMax"],
            "offerCount": len(p["variants"]),
            "availability": "https://schema.org/InStock" if p["available"] else "https://schema.org/OutOfStock",
        },
    }
    return json.dumps(data)


def render_product_page(p, catalog):
    desc_meta = (p["desc"][0][:155] if p["desc"] else
                 "Personal safety gear hand-packed by a U.S. veteran.")
    head = CHROME_HEAD.format(
        title=esc(p["title"] + " | Meli's Defense Boutique"),
        desc=esc(desc_meta),
        url=page_url(p),
        image=img_url(p),
        jsonld=jsonld_for(p),
        handle=esc(p["handle"]),
    )

    thumbs = "\n".join(
        '<button class="thumb thumb-photo" aria-label="Photo %d"><img loading="lazy" src="/%s" alt=""></button>'
        % (i + 1, esc(src)) if not src.startswith("http") else
        '<button class="thumb thumb-photo" aria-label="Photo %d"><img loading="lazy" src="%s" alt=""></button>'
        % (i + 1, esc(src))
        for i, src in enumerate(p["images"])
    )

    options_html = []
    for opt in p["options"]:
        chips = "".join('<button class="opt-chip%s">%s</button>'
                        % (" active" if i == 0 else "", esc(v))
                        for i, v in enumerate(opt["values"]))
        options_html.append(
            '<div class="opt-label">%s &mdash; <em>%s</em></div>'
            '<div class="opt-values" role="radiogroup" aria-label="Choose %s">%s</div>'
            % (esc(opt["name"]), esc(opt["values"][0]) if opt["values"] else "", esc(opt["name"]), chips))

    desc_paras_short = ("<p>%s</p>" % esc(p["desc"][0])) if p["desc"] else ""
    desc_paras_long = "\n".join("<p>%s</p>" % esc(d) for d in (p["desc"][1:] if len(p["desc"]) > 1 else p["desc"]))
    if not p["desc"]:
        desc_paras_long = "<p>Hand-picked by Melissa for the lineup. Questions? Ask her directly &mdash; she answers.</p>"

    price_str = "$%.2f" % p["price"]
    main_src = p["images"][0] if p["images"] else ""
    main_src_attr = esc(main_src) if main_src.startswith("http") else "/" + esc(main_src)

    cross = [x for x in catalog if x["handle"] != p["handle"]]
    cross.sort(key=lambda x: x["category"] != p["category"])
    cross_html = "\n".join(
        '<a class="card" href="/products/%s.html">'
        '<div class="art art-photo"><img loading="lazy" src="%s" alt="%s"></div>'
        '<div class="meta"><b>%s</b><div class="price">%s$%.2f</div></div></a>'
        % (esc(x["handle"]),
           (esc(x["images"][0]) if x["images"][0].startswith("http") else "/" + esc(x["images"][0])),
           esc(x["title"]), esc(x["title"]),
           "From " if x["priceMax"] > x["price"] else "", x["price"])
        for x in cross[:4]
    )

    body = """
<div class="wrap crumbs"><a href="/index.html">Home</a> / <a id="crumb-cat" href="/shop.html#{catslug}">{category}</a> / <span id="crumb-title">{title}</span></div>

<main class="wrap pdp">
  <div class="gallery">
    <div class="main-art art-photo" id="main-art">
      <img id="main-img" src="{main_src}" alt="{title}">
    </div>
    <div class="thumbs" id="thumbs">
{thumbs}
    </div>
  </div>

  <div class="buybox">
    <p class="eyebrow" id="p-category">{category}</p>
    <h1 id="p-title">{title}</h1>
    <div class="pprice"><span id="p-compare"></span><span id="p-price">{price}</span> <small>&middot; free US shipping over $100</small></div>

    <div id="p-desc-short">{desc_short}</div>

    <div id="p-options">
{options}
    </div>

    <div class="atc-row">
      <div class="qty" aria-label="Quantity">
        <button aria-label="Decrease quantity" id="qty-minus">&minus;</button>
        <output id="qty-out">1</output>
        <button aria-label="Increase quantity" id="qty-plus">+</button>
      </div>
      <button class="btn btn-pink" id="atc">Add to cart</button>
    </div>

    <ul class="ship-notes">
      <li><b>Packed by Melissa</b> &mdash; hand-assembled, ships in 5&ndash;7 business days</li>
      <li><b>Secure Shopify checkout</b> &mdash; payments, shipping, and taxes handled by her store</li>
      <li><b>Know your laws</b> &mdash; some tools have state restrictions; ask before you order</li>
    </ul>
  </div>
</main>

<section class="wrap desc-grid">
  <div>
    <h3>The details</h3>
    <div id="p-desc">
{desc_long}
    </div>
  </div>
  <div>
    <h3>Good to know</h3>
    <table class="spec-table">
      <tr><td>Ships</td><td>5&ndash;7 business days, packed by Melissa</td></tr>
      <tr><td>Free shipping</td><td>US orders $100+</td></tr>
      <tr><td>Checkout</td><td>Secure Shopify checkout</td></tr>
      <tr><td>Questions</td><td><a href="mailto:melisdefenseboutique@gmail.com">Ask Melissa directly</a></td></tr>
    </table>
    <div class="legal-note">
      <b>Legality note</b><br>
      Self-defense tools can carry state and age restrictions. You are responsible for
      knowing what's legal to carry where you live &mdash; see the
      <a href="/policies.html#restrictions">state shipping restrictions</a>, and when in doubt,
      <a href="mailto:melisdefenseboutique@gmail.com">ask before ordering</a>.
    </div>
  </div>
</section>

<section class="block" style="padding-top: 0;">
  <div class="wrap">
    <p class="eyebrow">Complete your set</p>
    <h2 class="title">Goes great with</h2>
    <div class="grid4" id="cross-sell">
{cross}
    </div>
  </div>
</section>
""".format(
        catslug=esc(p["catSlug"]), category=esc(p["category"]), title=esc(p["title"]),
        main_src=main_src_attr, thumbs=thumbs, price=price_str,
        desc_short=desc_paras_short, options="\n".join(options_html),
        desc_long=desc_paras_long, cross=cross_html,
    )
    return head + body + CHROME_FOOT


def write_sitemap(catalog):
    today = datetime.date.today().isoformat()
    urls = [
        (BASE + "/", "daily"),
        (BASE + "/shop.html", "daily"),
        (BASE + "/policies.html", "monthly"),
        (BASE + "/are-self-defense-keychains-legal.html", "monthly"),
    ] + [(page_url(p), "daily") for p in catalog]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, freq in urls:
        lines.append("  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq></url>"
                     % (esc(url), today, freq))
    lines.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")


def write_merchant_feed(catalog):
    items = []
    skipped = []
    for p in catalog:
        if not feed_eligible(p):
            skipped.append(p["title"])
            continue
        desc = " ".join(p["desc"])[:4900] or "Personal safety accessory from Meli's Defense Boutique."
        items.append("""  <item>
    <g:id>%s</g:id>
    <g:title>%s</g:title>
    <g:description>%s</g:description>
    <g:link>%s</g:link>
    <g:image_link>%s</g:image_link>
    <g:availability>%s</g:availability>
    <g:price>%.2f USD</g:price>
    <g:condition>new</g:condition>
    <g:brand>Meli's Defense Boutique</g:brand>
    <g:identifier_exists>no</g:identifier_exists>
  </item>""" % (esc(p["handle"]), esc(p["title"]), esc(desc), esc(page_url(p)),
                esc(img_url(p)), "in_stock" if p["available"] else "out_of_stock", p["price"]))
    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
<channel>
  <title>Meli's Defense Boutique</title>
  <link>%s</link>
  <description>Self-defense keychains and safety accessories, hand-packed by a U.S. veteran.</description>
%s
</channel>
</rss>
""" % (BASE, "\n".join(items))
    open(os.path.join(ROOT, "merchant-feed.xml"), "w", encoding="utf-8", newline="\n").write(feed)
    return len(items), skipped


def main():
    catalog = load_catalog()
    os.makedirs(PRODUCTS_DIR, exist_ok=True)

    expected = set()
    for p in catalog:
        fname = p["handle"] + ".html"
        expected.add(fname)
        with open(os.path.join(PRODUCTS_DIR, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(render_product_page(p, catalog))
    for f in os.listdir(PRODUCTS_DIR):
        if f.endswith(".html") and f not in expected:
            os.remove(os.path.join(PRODUCTS_DIR, f))

    write_sitemap(catalog)
    n_feed, skipped = write_merchant_feed(catalog)
    print("product pages: %d | sitemap urls: %d | merchant feed items: %d"
          % (len(catalog), len(catalog) + 4, n_feed))
    print("excluded from merchant feed (Google Shopping weapons policy):")
    for t in skipped:
        print("  -", t)


if __name__ == "__main__":
    main()
