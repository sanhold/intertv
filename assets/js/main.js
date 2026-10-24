// INTER TV — scripts partagés

document.addEventListener('DOMContentLoaded', () => {
  // Menu mobile
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('open');
      toggle.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open);
    });
    links.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => { links.classList.remove('open'); toggle.classList.remove('open'); });
    });
  }

  // Marque le lien de navigation actif selon la page courante
  const current = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach((link) => {
    const href = link.getAttribute('href');
    if (href === current) link.classList.add('active');
  });

  // Lecteur YouTube : bascule direct / dernières vidéos (?live ouvre directement le direct)
  const player = document.querySelector('#yt-player');
  const tabs = document.querySelectorAll('.player-tab');
  if (player && tabs.length) {
    const select = (tab) => {
      tabs.forEach((t) => t.classList.toggle('active', t === tab));
      player.src = tab.dataset.src;
    };
    tabs.forEach((tab) => tab.addEventListener('click', () => select(tab)));
    if (new URLSearchParams(window.location.search).has('live')) select(tabs[0]);
  }

  // Lecteur vidéo en fenêtre modale : les vidéos YouTube se lisent sur le site
  const modal = document.createElement('div');
  modal.className = 'video-modal';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-hidden', 'true');
  modal.innerHTML = `
    <div class="video-modal-box">
      <button type="button" class="video-modal-close" aria-label="Fermer"><i class="fa-solid fa-xmark"></i></button>
      <div class="video-modal-frame"></div>
      <div class="video-modal-bar">
        <span class="video-modal-title"></span>
        <a class="btn btn--youtube btn--sm" target="_blank" rel="noopener"><i class="fa-brands fa-youtube"></i> Voir sur YouTube</a>
      </div>
    </div>`;
  document.body.appendChild(modal);
  const frame = modal.querySelector('.video-modal-frame');
  const ytLink = modal.querySelector('.video-modal-bar a');
  const ytTitle = modal.querySelector('.video-modal-title');
  let lastFocus = null;

  const closeModal = () => {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    frame.innerHTML = '';
    document.body.classList.remove('modal-open');
    if (lastFocus) lastFocus.focus();
  };
  const openModal = (id, title) => {
    frame.innerHTML = `<iframe src="https://www.youtube.com/embed/${id}?autoplay=1&rel=0" title="${title.replace(/"/g, '&quot;')}" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>`;
    ytLink.href = `https://www.youtube.com/watch?v=${id}`;
    ytTitle.textContent = title;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    modal.querySelector('.video-modal-close').focus();
  };

  document.querySelectorAll('a.video-card').forEach((card) => {
    card.addEventListener('click', (e) => {
      const m = card.href.match(/[?&]v=([\w-]{11})/);
      if (window.location.protocol === 'file:') return; // YouTube refuse l'intégration hors http(s) : on ouvre YouTube
      if (!m || e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1) return; // ouverture en onglet : comportement normal
      e.preventDefault();
      lastFocus = card;
      openModal(m[1], card.querySelector('h3')?.textContent.trim() || 'Vidéo Inter TV');
    });
  });
  modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  modal.querySelector('.video-modal-close').addEventListener('click', closeModal);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && modal.classList.contains('open')) closeModal(); });

  // Formulaire de contact : envoi par e-mail via FormSubmit (https://formsubmit.co)
  const contactForm = document.querySelector('#contact-form');
  if (contactForm) {
    const alertBox = document.querySelector('#contact-alert');
    const submitBtn = contactForm.querySelector('button[type="submit"]');
    const showAlert = (ok, text) => {
      if (!alertBox) return;
      alertBox.className = `alert show ${ok ? 'alert--success' : 'alert--error'}`;
      alertBox.textContent = text;
      alertBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const label = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Envoi en cours…';
      try {
        const res = await fetch(contactForm.action.replace('formsubmit.co/', 'formsubmit.co/ajax/'), {
          method: 'POST',
          headers: { Accept: 'application/json' },
          body: new FormData(contactForm),
        });
        const data = await res.json();
        if (!res.ok || String(data.success) !== 'true') throw new Error(data.message || 'Échec');
        showAlert(true, 'Merci, votre message a bien été envoyé. Notre équipe vous répondra rapidement.');
        contactForm.reset();
      } catch (err) {
        showAlert(false, "Le message n'a pas pu être envoyé. Réessayez ou écrivez-nous directement à intertvci@gmail.com.");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = label;
      }
    });
  }

  // Filtrage simple des programmes par rubrique
  const pills = document.querySelectorAll('[data-filter]');
  const items = document.querySelectorAll('[data-category]');
  if (pills.length && items.length) {
    pills.forEach((pill) => {
      pill.addEventListener('click', () => {
        pills.forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');
        const filter = pill.getAttribute('data-filter');
        items.forEach((item) => {
          const show = filter === 'all' || item.getAttribute('data-category') === filter;
          item.style.display = show ? '' : 'none';
        });
      });
    });
  }
});
