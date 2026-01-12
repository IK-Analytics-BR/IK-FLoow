document.addEventListener('DOMContentLoaded', function () {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const navLinks = Array.from(document.querySelectorAll('.top-nav-links a'));

  function setActiveLinkForSlideId(id) {
    navLinks.forEach((link) => {
      const href = link.getAttribute('href') || '';
      const targetId = href.startsWith('#') ? href.slice(1) : null;
      if (targetId && targetId === id) {
        link.classList.add('is-active');
      } else {
        link.classList.remove('is-active');
      }

  // Navegação por hover: ao passar o mouse no link, rola até o slide
  navLinks.forEach((link) => {
    link.addEventListener('mouseenter', (event) => {
      const href = link.getAttribute('href') || '';
      if (!href.startsWith('#')) return;

      const targetId = href.slice(1);
      const targetSlide = document.getElementById(targetId);
      if (!targetSlide) return;

      // Usa scroll suave até o início do slide
      targetSlide.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
    });
  }

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const slide = entry.target;
          if (entry.isIntersecting) {
            slide.classList.add('slide--visible');
            setActiveLinkForSlideId(slide.id);
          } else {
            slide.classList.remove('slide--visible');
          }
        });
      },
      {
        threshold: 0.35,
      }
    );

    slides.forEach((slide) => observer.observe(slide));
  } else {
    // Fallback simples: marca o primeiro slide como visível
    if (slides[0]) {
      slides[0].classList.add('slide--visible');
      setActiveLinkForSlideId(slides[0].id);
    }
  }
});
