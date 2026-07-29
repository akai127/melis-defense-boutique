/* Meli's Defense Boutique — shared cart.
   Items live in localStorage; checkout hands the cart to Shopify via a
   cart permalink, so payment/shipping/taxes run on the existing store. */
(function () {
  var STORE = "https://melis-defense-boutique.myshopify.com";
  var KEY = "mdb_cart";
  var FREE_SHIP = 100;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; }
    catch (e) { return []; }
  }
  function save(items) {
    localStorage.setItem(KEY, JSON.stringify(items));
    renderCount(items);
    renderDrawer(items);
  }
  function count(items) {
    return items.reduce(function (n, it) { return n + it.qty; }, 0);
  }
  function subtotal(items) {
    return items.reduce(function (n, it) { return n + it.qty * it.price; }, 0);
  }
  function money(n) {
    return "$" + n.toFixed(2);
  }
  function checkoutUrl(items) {
    var parts = items.map(function (it) { return it.id + ":" + it.qty; });
    return STORE + "/cart/" + parts.join(",");
  }

  function renderCount(items) {
    var n = count(items);
    document.querySelectorAll(".cart-open").forEach(function (el) {
      el.setAttribute("aria-label", "Cart, " + n + " items");
      var label = el.querySelector(".cart-count");
      if (label) label.textContent = "(" + n + ")";
    });
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function renderDrawer(items) {
    var body = document.querySelector(".drawer-body");
    var foot = document.querySelector(".drawer-foot");
    if (!body || !foot) return;
    body.innerHTML = "";
    foot.innerHTML = "";

    if (!items.length) {
      var empty = el("div", "drawer-empty");
      empty.appendChild(el("b", null, "Your bag is empty"));
      empty.appendChild(el("p", null, "Every keychain says “text me when you’re home.”"));
      var go = el("a", "btn btn-pink", "Shop the lineup");
      go.href = "shop.html";
      empty.appendChild(go);
      body.appendChild(empty);
      return;
    }

    items.forEach(function (it) {
      var row = el("div", "drawer-item");
      var img = el("img");
      img.src = it.img || "";
      img.alt = it.title;
      row.appendChild(img);

      var info = el("div", "drawer-info");
      info.appendChild(el("b", null, it.title));
      if (it.vtitle && it.vtitle !== "Default Title") {
        info.appendChild(el("span", "drawer-variant", it.vtitle));
      }
      info.appendChild(el("span", "drawer-price", money(it.price)));

      var qty = el("div", "qty drawer-qty");
      var minus = el("button", null, "−");
      minus.setAttribute("aria-label", "Decrease quantity");
      var out = el("output", null, String(it.qty));
      var plus = el("button", null, "+");
      plus.setAttribute("aria-label", "Increase quantity");
      minus.addEventListener("click", function () { changeQty(it.id, -1); });
      plus.addEventListener("click", function () { changeQty(it.id, 1); });
      qty.appendChild(minus); qty.appendChild(out); qty.appendChild(plus);
      info.appendChild(qty);
      row.appendChild(info);

      var rm = el("button", "drawer-remove", "×");
      rm.setAttribute("aria-label", "Remove " + it.title);
      rm.addEventListener("click", function () { removeItem(it.id); });
      row.appendChild(rm);
      body.appendChild(row);
    });

    var sub = subtotal(items);
    var ship = el("div", "drawer-ship");
    if (sub >= FREE_SHIP) {
      ship.textContent = "Free US shipping unlocked!";
      ship.classList.add("unlocked");
    } else {
      ship.textContent = money(FREE_SHIP - sub) + " away from free US shipping";
    }
    foot.appendChild(ship);

    var totalRow = el("div", "drawer-total");
    totalRow.appendChild(el("span", null, "Subtotal"));
    totalRow.appendChild(el("b", null, money(sub)));
    foot.appendChild(totalRow);

    var checkout = el("a", "btn btn-pink drawer-checkout", "Checkout");
    checkout.href = checkoutUrl(items);
    foot.appendChild(checkout);
    foot.appendChild(el("p", "drawer-note", "Secure Shopify checkout"));
  }

  function changeQty(id, delta) {
    var items = load();
    var it = items.find(function (x) { return x.id === id; });
    if (!it) return;
    it.qty += delta;
    if (it.qty <= 0) items = items.filter(function (x) { return x.id !== id; });
    save(items);
  }
  function removeItem(id) {
    save(load().filter(function (x) { return x.id !== id; }));
  }

  function open() {
    document.body.classList.add("drawer-is-open");
  }
  function close() {
    document.body.classList.remove("drawer-is-open");
  }

  function build() {
    var overlay = el("div", "drawer-overlay");
    overlay.addEventListener("click", close);

    var drawer = el("aside", "cart-drawer");
    drawer.setAttribute("aria-label", "Shopping bag");
    var head = el("div", "drawer-head");
    head.appendChild(el("b", null, "Your bag"));
    var x = el("button", "drawer-close", "×");
    x.setAttribute("aria-label", "Close bag");
    x.addEventListener("click", close);
    head.appendChild(x);
    drawer.appendChild(head);
    drawer.appendChild(el("div", "drawer-body"));
    drawer.appendChild(el("div", "drawer-foot"));

    document.body.appendChild(overlay);
    document.body.appendChild(drawer);

    document.querySelectorAll(".cart-open").forEach(function (elx) {
      elx.addEventListener("click", function (e) { e.preventDefault(); open(); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
  }

  window.MDBCart = {
    add: function (item) {
      var items = load();
      var existing = items.find(function (x) { return x.id === item.id; });
      if (existing) existing.qty += item.qty;
      else items.push(item);
      save(items);
      open();
    },
    open: open,
    close: close,
  };

  document.addEventListener("DOMContentLoaded", function () {
    build();
    var items = load();
    renderCount(items);
    renderDrawer(items);
  });
})();
