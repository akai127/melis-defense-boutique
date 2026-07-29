/* Product-page hydration. Works on prerendered /products/<handle>.html pages
   (handle from <body data-handle>) and the legacy p.html?h= router. */
(function () {
  var R = window.MDBRender;
  var handle = document.body.dataset.handle ||
    new URLSearchParams(location.search).get("h");
  var product = R.byHandle(handle);
  if (!product) { location.replace("/shop.html"); return; }

  document.title = product.title + " | Meli's Defense Boutique";
  var crumbCat = document.getElementById("crumb-cat");
  crumbCat.textContent = product.category;
  crumbCat.href = "/shop.html#" + product.catSlug;
  document.getElementById("crumb-title").textContent = product.title;
  document.getElementById("p-category").textContent = product.category;
  document.getElementById("p-title").textContent = product.title;
  document.getElementById("sticky-title").textContent = product.title;

  var shortEl = document.getElementById("p-desc-short");
  var longEl = document.getElementById("p-desc");
  shortEl.innerHTML = "";
  longEl.innerHTML = "";
  if (product.desc.length) {
    var p0 = document.createElement("p");
    p0.textContent = product.desc[0];
    shortEl.appendChild(p0);
  }
  (product.desc.length > 1 ? product.desc.slice(1) : product.desc).forEach(function (para) {
    var p = document.createElement("p");
    p.textContent = para;
    longEl.appendChild(p);
  });
  if (!product.desc.length) {
    var pd = document.createElement("p");
    pd.textContent = "Hand-picked by Melissa for the lineup. Questions? Ask her directly — she answers.";
    longEl.appendChild(pd);
  }

  var mainImg = document.getElementById("main-img");
  var thumbs = document.getElementById("thumbs");
  thumbs.innerHTML = "";
  function showImage(i) {
    mainImg.src = R.imgUrl(product.images[i], 1100);
    mainImg.alt = product.title + " — photo " + (i + 1);
    Array.prototype.forEach.call(thumbs.children, function (t, j) {
      t.classList.toggle("active", j === i);
    });
  }
  product.images.forEach(function (src, i) {
    var t = document.createElement("button");
    t.className = "thumb thumb-photo";
    t.setAttribute("aria-label", "Photo " + (i + 1));
    var im = document.createElement("img");
    im.loading = "lazy";
    im.src = R.imgUrl(src, 220);
    im.alt = "";
    t.appendChild(im);
    t.addEventListener("click", function () { showImage(i); });
    thumbs.appendChild(t);
  });

  var selection = product.options.map(function (o) { return o.values[0]; });
  var optsWrap = document.getElementById("p-options");
  function currentVariant() {
    for (var i = 0; i < product.variants.length; i++) {
      var v = product.variants[i];
      var match = true;
      for (var j = 0; j < selection.length; j++) {
        if (v.opts[j] !== selection[j]) { match = false; break; }
      }
      if (match) return v;
    }
    return null;
  }
  function renderOptions() {
    optsWrap.innerHTML = "";
    product.options.forEach(function (opt, i) {
      var label = document.createElement("div");
      label.className = "opt-label";
      label.appendChild(document.createTextNode(opt.name + " — "));
      var em = document.createElement("em");
      em.textContent = selection[i];
      label.appendChild(em);
      optsWrap.appendChild(label);
      var group = document.createElement("div");
      group.className = "opt-values";
      group.setAttribute("role", "radiogroup");
      group.setAttribute("aria-label", "Choose " + opt.name);
      opt.values.forEach(function (val) {
        var b = document.createElement("button");
        b.className = "opt-chip" + (selection[i] === val ? " active" : "");
        b.textContent = val;
        b.addEventListener("click", function () {
          selection[i] = val;
          renderOptions();
          updateBuyState();
        });
        group.appendChild(b);
      });
      optsWrap.appendChild(group);
    });
  }

  var qty = 1;
  var qtyOut = document.getElementById("qty-out");
  document.getElementById("qty-minus").addEventListener("click", function () {
    if (qty > 1) { qty--; qtyOut.textContent = qty; updateBuyState(); }
  });
  document.getElementById("qty-plus").addEventListener("click", function () {
    qty++; qtyOut.textContent = qty; updateBuyState();
  });

  var atc = document.getElementById("atc");
  var stickyAtc = document.getElementById("sticky-atc-btn");
  function updateBuyState() {
    var v = currentVariant();
    var priceEl = document.getElementById("p-price");
    var compareEl = document.getElementById("p-compare");
    if (!v) {
      priceEl.textContent = "$" + product.price.toFixed(2);
      compareEl.textContent = "";
      atc.textContent = "Unavailable";
      atc.disabled = true;
      stickyAtc.disabled = true;
      return;
    }
    priceEl.textContent = "$" + v.price.toFixed(2);
    compareEl.innerHTML = v.compare && v.compare > v.price
      ? "<s>$" + v.compare.toFixed(2) + "</s> " : "";
    document.getElementById("sticky-price").textContent =
      "$" + v.price.toFixed(2) + (v.title !== "Default Title" ? " · " + v.title : "");
    if (v.img != null) showImage(v.img);
    if (!v.available) {
      atc.textContent = "Sold out";
      atc.disabled = true;
      stickyAtc.disabled = true;
    } else {
      atc.textContent = "Add to cart — $" + (v.price * qty).toFixed(2);
      atc.disabled = false;
      stickyAtc.disabled = false;
    }
  }
  function addToCart() {
    var v = currentVariant();
    if (!v || !v.available) return;
    window.MDBCart.add({
      id: v.id,
      qty: qty,
      handle: product.handle,
      title: product.title,
      vtitle: v.title,
      price: v.price,
      img: R.imgUrl(product.images[v.img != null ? v.img : 0], 220),
    });
  }
  atc.addEventListener("click", addToCart);
  stickyAtc.addEventListener("click", addToCart);

  var cross = window.CATALOG
    .filter(function (p) { return p.handle !== product.handle; })
    .sort(function (a, b) {
      return (b.category === product.category) - (a.category === product.category);
    })
    .slice(0, 4);
  var crossWrap = document.getElementById("cross-sell");
  crossWrap.innerHTML = "";
  cross.forEach(function (p) { crossWrap.appendChild(R.productCard(p)); });

  showImage(0);
  renderOptions();
  updateBuyState();
})();
