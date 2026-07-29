/* Shared render helpers — product cards built from window.CATALOG. */
(function () {
  function imgUrl(src, width) {
    // local repo images are pre-sized; only CDN URLs take a width param
    if (src.indexOf("http") !== 0) return src;
    return src + (src.indexOf("?") === -1 ? "?" : "&") + "width=" + width;
  }

  function priceHtml(p) {
    var out = "";
    if (p.compare && p.compare > p.price) {
      out += "<s>$" + p.compare.toFixed(2) + "</s>";
    }
    out += (p.priceMax > p.price ? "From " : "") + "$" + p.price.toFixed(2);
    return out;
  }

  function productCard(p) {
    var a = document.createElement("a");
    a.className = "card";
    a.href = "p.html?h=" + encodeURIComponent(p.handle);
    var flag = "";
    if (!p.available) flag = '<span class="flag">Sold out</span>';
    else if (p.compare && p.compare > p.price) flag = '<span class="flag">Sale</span>';
    a.innerHTML =
      flag +
      '<div class="art art-photo"><img loading="lazy" alt="" src="' + imgUrl(p.images[0], 640) + '"></div>' +
      '<div class="meta"><b></b><div class="price">' + priceHtml(p) + "</div></div>";
    a.querySelector(".art img").alt = p.title;
    a.querySelector(".meta b").textContent = p.title;
    return a;
  }

  function byHandle(handle) {
    for (var i = 0; i < window.CATALOG.length; i++) {
      if (window.CATALOG[i].handle === handle) return window.CATALOG[i];
    }
    return null;
  }

  window.MDBRender = { imgUrl: imgUrl, priceHtml: priceHtml, productCard: productCard, byHandle: byHandle };
})();
