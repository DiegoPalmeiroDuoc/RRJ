/* HospitalOps: navegación con skeletons, carga diferida del dashboard y pequeños helpers. */
(() => {
  'use strict';
  const skeleton = document.getElementById('page-skeleton');
  let started = false;
  const showSkeleton = () => {
    if (started || !skeleton) return;
    started = true;
    skeleton.classList.add('is-loading');
    skeleton.setAttribute('aria-hidden', 'false');
  };
  window.addEventListener('pageshow', () => {
    started = false;
    skeleton?.classList.remove('is-loading');
    skeleton?.setAttribute('aria-hidden', 'true');
  });
  document.addEventListener('click', e => {
    const link = e.target.closest('a[href]');
    if (!link || link.dataset.noSkeleton !== undefined || link.hasAttribute('download') ||
        e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || link.target === '_blank') return;
    const href = link.getAttribute('href');
    if (href?.startsWith('/') && !href.startsWith('//') && href !== location.pathname && !href.includes('#')) showSkeleton();
  });
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', e => {
      if (e.defaultPrevented) return;
      const button = e.submitter;
      if (button) { button.disabled = true; button.dataset.originalText = button.textContent; button.textContent = 'Procesando…'; }
    });
  });
  const toggle = document.getElementById('menu-toggle');
  toggle?.addEventListener('click', () => document.getElementById('sidebar')?.classList.toggle('open'));
  document.addEventListener('click', e => {
    const sidebar = document.getElementById('sidebar');
    if (sidebar?.classList.contains('open') && !sidebar.contains(e.target) && !toggle?.contains(e.target)) sidebar.classList.remove('open');
  });
  // Lectura opcional de códigos EAN/Code128 con la API nativa del navegador.
  // Sin soporte o permisos de cámara, el ingreso manual o escáner USB sigue disponible.
  let scanStream = null;
  let scanFrame = null;
  const stopScanner = () => {
    if (scanFrame !== null) cancelAnimationFrame(scanFrame);
    scanFrame = null;
    scanStream?.getTracks().forEach(t => t.stop());
    scanStream = null;
  };
  document.querySelectorAll('[data-scan-target]').forEach(button => {
    button.addEventListener('click', async () => {
      const target = document.querySelector(button.dataset.scanTarget);
      if (!target) return;
      if (!('BarcodeDetector' in window) || !navigator.mediaDevices?.getUserMedia) {
        alert('La lectura con cámara no está disponible en este navegador. Escribe el código o utiliza un escáner USB.');
        target.focus();
        return;
      }
      const dialog = document.createElement('dialog');
      dialog.className = 'barcode-dialog';
      dialog.innerHTML = '<h2>Escanear código de barras</h2><p>Apunta la cámara al código del producto.</p><video autoplay muted playsinline></video><div class="barcode-status">Iniciando cámara…</div><button type="button" class="btn btn-secondary">Cancelar</button>';
      document.body.appendChild(dialog);
      const close = () => { stopScanner(); if (dialog.open) dialog.close(); dialog.remove(); };
      dialog.querySelector('button').addEventListener('click', close);
      dialog.addEventListener('close', close);
      dialog.showModal();
      try {
        scanStream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'},audio:false});
        const video = dialog.querySelector('video');
        video.srcObject = scanStream;
        await video.play();
        const detector = new window.BarcodeDetector();
        let running = false;
        const scan = async () => {
          if (!dialog.open || running) return;
          running = true;
          try {
            const codes = await detector.detect(video);
            if (codes.length > 0) {
              target.value = codes[0].rawValue;
              target.dispatchEvent(new Event('input',{bubbles:true}));
              close();
              target.focus();
              return;
            }
          } catch (_) { /* fallback to next frame */ }
          running = false;
          if (dialog.open) scanFrame = requestAnimationFrame(scan);
        };
        dialog.querySelector('.barcode-status').textContent = 'Buscando código…';
        scanFrame = requestAnimationFrame(scan);
      } catch (_) {
        dialog.querySelector('.barcode-status').textContent = 'No se pudo acceder a la cámara. Autoriza el permiso o ingresa el código manualmente.';
      }
    });
  });
  const dashboard = document.getElementById('dashboard-stats');
  if (dashboard?.dataset.asyncDashboard === '1') {
    fetch('/api/dashboard', {credentials:'same-origin',headers:{'Accept':'application/json'},cache:'no-store'})
      .then(response => { if (!response.ok) throw Error('Dashboard unavailable'); return response.json(); })
      .then(stats => Object.entries(stats).forEach(([key,value]) => {
        const target = dashboard.querySelector(`[data-stat="${key}"]`);
        if (target) target.textContent = new Intl.NumberFormat('es-CL').format(value);
      }))
      .catch(() => dashboard.querySelectorAll('[data-stat]').forEach(target => { target.textContent = '—'; }));
  }
  const movementKind = document.getElementById('movement-kind');
  const amountLabel = document.getElementById('amount-label');
  const updateKind = () => { if (movementKind && amountLabel) amountLabel.childNodes[0].textContent = movementKind.value === 'ajuste' ? 'Stock final deseado' : 'Cantidad de unidades'; };
  movementKind?.addEventListener('change', updateKind);
  updateKind();
  document.querySelectorAll('.count-input').forEach(input => {
    const update = () => {
      const delta = Number(input.value) - Number(input.dataset.expected);
      const diff = input.closest('tr')?.querySelector('.count-difference');
      if (diff) { diff.textContent = (delta > 0 ? '+' : '') + delta; diff.className = 'count-difference ' + (delta < 0 ? 'negative' : delta > 0 ? 'positive' : ''); }
    };
    input.addEventListener('input', update);
  });
})();

// Acciones sin manejadores inline (compatibles con una CSP restrictiva).
document.addEventListener('change', (ev) => {
  if (ev.target.matches('[data-auto-submit]') && ev.target.form) ev.target.form.requestSubmit();
});
document.addEventListener('click', (ev) => {
  const button = ev.target.closest('[data-dismiss-alert]');
  if (button) button.closest('.alert')?.remove();
});
