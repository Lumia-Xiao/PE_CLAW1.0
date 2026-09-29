const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');

if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });

  navLinks.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

document.querySelectorAll('.copy-button').forEach((button) => {
  button.addEventListener('click', async () => {
    const text = button.dataset.copy || '';
    try {
      await navigator.clipboard.writeText(text);
      const original = button.textContent;
      button.textContent = 'Copied';
      setTimeout(() => { button.textContent = original; }, 1400);
    } catch {
      button.textContent = 'Copy failed';
      setTimeout(() => { button.textContent = 'Copy'; }, 1400);
    }
  });
});

const caseTabs = Array.from(document.querySelectorAll('.case-tab'));
const casePanels = Array.from(document.querySelectorAll('.case-panel'));

function activateCase(activeTab, moveFocus = false) {
  const targetId = activeTab.dataset.caseTarget;

  caseTabs.forEach((tab) => {
    const isActive = tab === activeTab;
    tab.classList.toggle('is-active', isActive);
    tab.setAttribute('aria-selected', String(isActive));
    tab.tabIndex = isActive ? 0 : -1;
  });

  casePanels.forEach((panel) => {
    const isActive = panel.id === targetId;
    panel.hidden = !isActive;
    panel.classList.toggle('is-active', isActive);
  });

  if (moveFocus) activeTab.focus();
}

caseTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => activateCase(tab));
  tab.addEventListener('keydown', (event) => {
    let nextIndex;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      nextIndex = (index + 1) % caseTabs.length;
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      nextIndex = (index - 1 + caseTabs.length) % caseTabs.length;
    } else if (event.key === 'Home') {
      nextIndex = 0;
    } else if (event.key === 'End') {
      nextIndex = caseTabs.length - 1;
    } else {
      return;
    }

    event.preventDefault();
    activateCase(caseTabs[nextIndex], true);
  });
});

const lightbox = document.querySelector('.lightbox');
const lightboxImage = lightbox?.querySelector('img');
const lightboxClose = lightbox?.querySelector('.lightbox-close');

function closeLightbox() {
  if (!lightbox || !lightboxImage) return;
  lightbox.classList.remove('open');
  lightbox.setAttribute('aria-hidden', 'true');
  lightboxImage.src = '';
  document.body.style.overflow = '';
}

document.querySelectorAll('[data-lightbox]').forEach((button) => {
  button.addEventListener('click', () => {
    if (!lightbox || !lightboxImage) return;
    lightboxImage.src = button.dataset.lightbox;
    lightbox.classList.add('open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  });
});

lightboxClose?.addEventListener('click', closeLightbox);
lightbox?.addEventListener('click', (event) => {
  if (event.target === lightbox) closeLightbox();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeLightbox();
});
