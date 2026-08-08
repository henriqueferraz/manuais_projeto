(function () {
  function initProductGallery(root) {
    var gallery = root.querySelector("#product-gallery") || document.getElementById("product-gallery");
    var thumbs = root.querySelectorAll(".tp-product-gallery__thumb");
    var lightbox = root.querySelector("#product-lightbox") || document.getElementById("product-lightbox");
    var lightboxImg = lightbox && lightbox.querySelector(".tp-product-lightbox__img");
    var lastFocus = null;

    if (gallery && thumbs.length) {
      gallery.addEventListener("slid.bs.carousel", function (event) {
        thumbs.forEach(function (thumb, index) {
          var active = index === event.to;
          thumb.classList.toggle("is-active", active);
          thumb.setAttribute("aria-current", active ? "true" : "false");
        });
      });
    }

    function activeZoomSource() {
      return (
        root.querySelector(".carousel-item.active [data-tp-gallery-zoom]") ||
        root.querySelector("[data-tp-gallery-zoom]")
      );
    }

    function openLightbox(src, alt) {
      if (!lightbox || !lightboxImg || !src) return;
      lastFocus = document.activeElement;
      lightboxImg.src = src;
      lightboxImg.alt = alt || "Foto ampliada";
      lightbox.hidden = false;
      document.body.classList.add("tp-product-lightbox-open");
      if (lightbox.parentElement !== document.body) {
        document.body.appendChild(lightbox);
      }
      var closeBtn = lightbox.querySelector(".tp-product-lightbox__close");
      if (closeBtn) closeBtn.focus();
    }

    function closeLightbox() {
      if (!lightbox || lightbox.hidden) return;
      lightbox.hidden = true;
      if (lightboxImg) {
        lightboxImg.removeAttribute("src");
        lightboxImg.alt = "";
      }
      document.body.classList.remove("tp-product-lightbox-open");
      if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
    }

    root.addEventListener("click", function (event) {
      var zoomBtn = event.target.closest("[data-tp-gallery-zoom-btn]");
      if (zoomBtn && root.contains(zoomBtn)) {
        event.preventDefault();
        var source = activeZoomSource();
        if (source) {
          openLightbox(source.getAttribute("data-zoom-src"), source.getAttribute("data-zoom-alt"));
        }
        return;
      }

      var hit = event.target.closest("[data-tp-gallery-zoom]");
      if (hit && root.contains(hit)) {
        event.preventDefault();
        openLightbox(hit.getAttribute("data-zoom-src"), hit.getAttribute("data-zoom-alt"));
      }
    });

    if (lightbox) {
      lightbox.addEventListener("click", function (event) {
        if (event.target.closest("[data-tp-lightbox-close]")) {
          event.preventDefault();
          closeLightbox();
        }
      });
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeLightbox();
    });
  }

  function boot() {
    document.querySelectorAll(".tp-product-gallery").forEach(initProductGallery);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
