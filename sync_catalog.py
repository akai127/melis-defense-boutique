"""Sync the static site's catalog from the live Shopify store.

Fetches products + collection memberships from the store's permanent
myshopify.com domain, regenerates catalog.js, downloads product images into
img/ (named by stable Shopify image id), and removes orphaned product images.
Runs both locally (from the repo root) and in GitHub Actions.

    python sync_catalog.py
"""
import html
import json
import os
import re
import subprocess
import sys
import time

STORE = "https://melis-defense-boutique.myshopify.com"
EXCLUDED_HANDLES = {"kitty-knuckles"}  # illegal to sell from VA (Va. Code 18.2-311)
IMG_KEEP = {"melissa-germany.jpg", "blog-pink-keychain.jpg"}  # non-product images

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "img")
OUT = os.path.join(ROOT, "catalog.js")

CATEGORY_ORDER = ["Self Defense Keychains", "Kid Friendly", "Add Ons", "Accessories"]
CATEGORY_SLUGS = {
    "Self Defense Keychains": "self-defense",
    "Kid Friendly": "kids",
    "Add Ons": "add-ons",
    "Accessories": "accessories",
}
COLLECTIONS = {
    "self-defense-keychains": "Self Defense Keychains",
    "kid-friendly-keychains": "Kid Friendly",
    "add-ons": "Add Ons",
    "accessories": "Accessories",
}


def curl(url, dest=None, attempts=4):
    """Fetch via curl — Shopify's edge fingerprint-blocks Python's HTTP stack.

    Retries with growing backoff on 429/5xx so a rate-limit blip doesn't fail
    the whole sync run.
    """
    cmd = ["curl", "-sfSL", "--max-time", "60", url]
    if dest:
        cmd += ["-o", dest]
    last_err = ""
    for attempt in range(attempts):
        if attempt:
            wait = 30 * (2 ** (attempt - 1))  # 30s, 60s, 120s
            print("retrying in %ds: %s" % (wait, url), file=sys.stderr)
            time.sleep(wait)
        result = subprocess.run(cmd, capture_output=True, timeout=90)
        if result.returncode == 0:
            return result.stdout
        last_err = result.stderr.decode(errors="replace")[:200]
        if "error: 4" in last_err and "429" not in last_err:
            break  # 403/404 etc. won't heal by waiting
    raise RuntimeError("curl failed for %s: %s" % (url, last_err))


def fetch_json(url):
    return json.loads(curl(url).decode("utf-8"))


def clean_desc(body_html):
    if not body_html:
        return []
    text = re.sub(r"<(br|/p|/div|/li)[^>]*>", "\n", body_html, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace(" ", " ").replace("​", "").replace("**", "")
    text = text.replace("’", "'").replace("�", "'")
    paras = [re.sub(r"\s+", " ", p).strip() for p in text.split("\n")]
    return [p for p in paras if p]


def ext_of(src):
    ext = os.path.splitext(src.split("?")[0])[1].lower()
    return ext if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif") else ".jpg"


def image_filename(handle, img):
    return "%s-%s%s" % (handle, img["id"], ext_of(img["src"]))


def download(url, dest):
    curl(url, dest=dest)
    if not (os.path.exists(dest) and os.path.getsize(dest) > 0):
        raise RuntimeError("empty download: %s" % url)


def main():
    products = fetch_json(STORE + "/products.json?limit=250")["products"]
    category = {}
    for slug, cat in COLLECTIONS.items():
        for p in fetch_json(STORE + "/collections/%s/products.json?limit=250" % slug)["products"]:
            category[p["handle"]] = cat
            if not any(x["handle"] == p["handle"] for x in products):
                products.append(p)

    os.makedirs(IMG_DIR, exist_ok=True)
    expected_files = set(IMG_KEEP)
    out = []
    downloaded = 0
    for p in products:
        if p["handle"] in EXCLUDED_HANDLES:
            continue
        images = []
        vid_to_img = {}
        for idx, img in enumerate(p["images"]):
            fname = image_filename(p["handle"], img)
            expected_files.add(fname)
            dest = os.path.join(IMG_DIR, fname)
            if not (os.path.exists(dest) and os.path.getsize(dest) > 0):
                url = img["src"] + ("&" if "?" in img["src"] else "?") + "width=1400"
                try:
                    download(url, dest)
                    downloaded += 1
                    time.sleep(0.15)
                except Exception as e:
                    print("WARN image failed %s: %s" % (fname, e), file=sys.stderr)
                    if not os.path.exists(dest):
                        # fall back to hotlinking the CDN for this image
                        images.append({"src": img["src"], "vids": img.get("variant_ids", [])})
                        for vid in img.get("variant_ids", []):
                            vid_to_img[vid] = idx
                        continue
            images.append({"src": "img/" + fname, "vids": img.get("variant_ids", [])})
            for vid in img.get("variant_ids", []):
                vid_to_img[vid] = idx

        variants = []
        prices = []
        for v in p["variants"]:
            price = float(v["price"])
            prices.append(price)
            compare = float(v["compare_at_price"]) if v.get("compare_at_price") else None
            variants.append({
                "id": v["id"],
                "title": v["title"],
                "price": price,
                "compare": compare,
                "available": bool(v.get("available")),
                "opts": [o for o in (v.get("option1"), v.get("option2"), v.get("option3")) if o is not None],
                "img": vid_to_img.get(v["id"]),
            })
        options = [
            {"name": o["name"], "values": o.get("values", [])}
            for o in p.get("options", [])
            if o.get("name", "").lower() != "title"
        ]
        for i, opt in enumerate(options):
            if not opt["values"]:
                seen = []
                for v in variants:
                    if i < len(v["opts"]) and v["opts"][i] not in seen:
                        seen.append(v["opts"][i])
                opt["values"] = seen
        cat = category.get(p["handle"], "Accessories")
        first_available = next((v for v in variants if v["available"]), variants[0])
        if not prices:
            continue
        out.append({
            "handle": p["handle"],
            "title": p["title"],
            "category": cat,
            "catSlug": CATEGORY_SLUGS[cat],
            "desc": clean_desc(p.get("body_html", "")),
            "price": min(prices),
            "priceMax": max(prices),
            "compare": first_available["compare"],
            "available": any(v["available"] for v in variants),
            "images": [img["src"] for img in images],
            "options": options,
            "variants": variants,
        })

    order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    out.sort(key=lambda p: (order[p["category"]], p["title"]))

    removed = 0
    for f in os.listdir(IMG_DIR):
        if f not in expected_files:
            os.remove(os.path.join(IMG_DIR, f))
            removed += 1

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("// Generated by sync_catalog.py — do not edit by hand.\n")
        f.write("// Snapshot of %s catalog.\n" % STORE)
        f.write("window.CATALOG = ")
        json.dump(out, f, separators=(",", ":"))
        f.write(";\n")
        f.write("window.CATEGORY_ORDER = %s;\n" % json.dumps(CATEGORY_ORDER))
        f.write("window.CATEGORY_SLUGS = %s;\n" % json.dumps(CATEGORY_SLUGS))

    print("products=%d images_downloaded=%d images_removed=%d" % (len(out), downloaded, removed))


if __name__ == "__main__":
    main()
