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

  // Função auxiliar para extrair o id de destino de um link do menu
  function getTargetIdFromLink(link) {
    const href = link.getAttribute('href') || '';
    return href.startsWith('#') ? href.slice(1) : null;
  }

  // Função auxiliar para rolar até um slide pelo id
  function goToSlideById(id) {
    if (!id) return;
    const targetSlide = document.getElementById(id);
    if (!targetSlide) return;
    targetSlide.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Atalhos de teclado:
  //  - tecla "k" avança para o próximo item de menu/slide
  //  - tecla "i" volta para o item anterior
  document.addEventListener('keydown', function (event) {
    const key = event.key || event.keyCode;

    // Determina direção com base na tecla: k = +1 (próximo), i = -1 (anterior)
    let direction = 0;
    if (key === 'k' || key === 'K' || key === 75) {
      direction = 1;
    } else if (key === 'i' || key === 'I' || key === 73) {
      direction = -1;
    } else {
      return; // tecla diferente de i/k: ignora
    }

    // Evita interferir se o usuário estiver digitando em algum campo
    const activeElement = document.activeElement;
    if (activeElement && (
      activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.isContentEditable
    )) {
      return;
    }

    if (!navLinks.length || !slides.length) return;

    // Slide atualmente visível (definido pelo IntersectionObserver)
    const visibleSlide = document.querySelector('.slide.slide--visible') || slides[0];
    if (!visibleSlide) return;

    const currentId = visibleSlide.id;
    const currentIndex = navLinks.findIndex(function (link) {
      return getTargetIdFromLink(link) === currentId;
    });

    if (currentIndex === -1) return;

    // Próximo ou anterior item de menu (cíclico)
    const nextIndex = (currentIndex + direction + navLinks.length) % navLinks.length;
    const nextLink = navLinks[nextIndex];
    const nextId = getTargetIdFromLink(nextLink);
    if (!nextId) return;

    event.preventDefault();
    goToSlideById(nextId);
  });

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
