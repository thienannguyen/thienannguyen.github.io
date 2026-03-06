(function () {
  var lightbox = document.getElementById('lightbox');
  var lightboxImg = lightbox && lightbox.querySelector('.lightbox__img');
  var backdrop = lightbox && lightbox.querySelector('.lightbox__backdrop');
  var closeBtn = lightbox && lightbox.querySelector('.lightbox__close');

  function openLightbox(src, alt) {
    if (!lightbox || !lightboxImg) return;
    lightboxImg.src = src;
    lightboxImg.alt = alt || '';
    lightbox.setAttribute('data-open', 'true');
    lightbox.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';
    closeBtn && closeBtn.focus();
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.setAttribute('data-open', 'false');
    lightbox.setAttribute('hidden', '');
    document.body.style.overflow = '';
  }

  function handleGalleryClick(e) {
    var link = e.target.closest('a.gallery-link');
    if (!link) return;
    var img = link.querySelector('img');
    if (!img || !img.src) return;
    e.preventDefault();
    openLightbox(img.src, img.alt);
  }

  function handleKeydown(e) {
    if (e.key === 'Escape' && lightbox && lightbox.getAttribute('data-open') === 'true') {
      closeLightbox();
    }
  }

  if (backdrop) backdrop.addEventListener('click', closeLightbox);
  if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
  document.addEventListener('keydown', handleKeydown);

  document.addEventListener('click', function (e) {
    if (e.target.closest('.gallery-link')) handleGalleryClick(e);
  });
})();
