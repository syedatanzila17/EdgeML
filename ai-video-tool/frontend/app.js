'use strict';

/* ─────────────────────────────
   Service Worker registration
───────────────────────────── */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}

/* ─────────────────────────────
   PWA install prompt
───────────────────────────── */
let _deferredInstall = null;
const installBtn = document.getElementById('install-btn');

window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  _deferredInstall = e;
  installBtn.classList.remove('hidden');
});

installBtn.addEventListener('click', async () => {
  if (!_deferredInstall) return;
  _deferredInstall.prompt();
  const { outcome } = await _deferredInstall.userChoice;
  if (outcome === 'accepted') {
    installBtn.classList.add('hidden');
    toast('App installed!');
  }
  _deferredInstall = null;
});

window.addEventListener('appinstalled', () => {
  installBtn.classList.add('hidden');
  _deferredInstall = null;
});

/* ─────────────────────────────
   Constants
───────────────────────────── */
const API_BASE = '/api';
const POLL_MS  = 2500;

/* ─────────────────────────────
   DOM refs
───────────────────────────── */
const formCard     = document.getElementById('form-card');
const progressCard = document.getElementById('progress-card');
const scriptCard   = document.getElementById('script-card');
const resultCard   = document.getElementById('result-card');
const errorCard    = document.getElementById('error-card');

const form        = document.getElementById('video-form');
const topicEl     = document.getElementById('topic');
const charCount   = document.getElementById('char-count');
const generateBtn = document.getElementById('generate-btn');

const statusDot   = document.getElementById('status-dot');
const statusLabel = document.getElementById('status-label');
const progBar     = document.getElementById('progress-bar');
const progPct     = document.getElementById('progress-pct');
const progTrack   = document.getElementById('prog-track');

const stepScript  = document.getElementById('step-script');
const stepVideo   = document.getElementById('step-video');
const stepDone    = document.getElementById('step-done');

const scriptContent = document.getElementById('script-content');
const downloadLink  = document.getElementById('download-link');
const errorMsg      = document.getElementById('error-msg');
const videoPlayer   = document.getElementById('video-player');

let pollTimer = null;

/* ─────────────────────────────
   Char counter
───────────────────────────── */
topicEl.addEventListener('input', () => {
  charCount.textContent = topicEl.value.length;
});

/* ─────────────────────────────
   Style card picker
───────────────────────────── */
const styleInput = document.getElementById('style');
document.getElementById('style-grid').addEventListener('click', e => {
  const card = e.target.closest('.style-card');
  if (!card) return;
  document.querySelectorAll('.style-card').forEach(c => {
    c.classList.remove('active');
    c.setAttribute('aria-pressed', 'false');
  });
  card.classList.add('active');
  card.setAttribute('aria-pressed', 'true');
  styleInput.value = card.dataset.value;
});

/* ─────────────────────────────
   Speed pills
───────────────────────────── */
const speedInput = document.getElementById('speed');
document.getElementById('speed-pills').addEventListener('click', e => {
  const pill = e.target.closest('.speed-pill');
  if (!pill) return;
  document.querySelectorAll('.speed-pill').forEach(p => p.classList.remove('active'));
  pill.classList.add('active');
  speedInput.value = pill.dataset.value;
});

/* ─────────────────────────────
   Show / hide cards
───────────────────────────── */
const ALL_CARDS = [formCard, progressCard, scriptCard, resultCard, errorCard];

function show(...cards) {
  ALL_CARDS.forEach(c => c.classList.add('hidden'));
  cards.forEach(c => c && c.classList.remove('hidden'));
  // Scroll to top of first visible card
  if (cards[0]) {
    setTimeout(() => cards[0].scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
  }
}

/* ─────────────────────────────
   Step indicators
───────────────────────────── */
const STEP_ORDER = ['generating_script', 'creating_video', 'completed'];
const STEP_ELS   = { generating_script: stepScript, creating_video: stepVideo, completed: stepDone };

function setStep(active) {
  STEP_ORDER.forEach((key, i) => {
    const el = STEP_ELS[key];
    el.classList.remove('active', 'done');
    const idx = STEP_ORDER.indexOf(active);
    if (i < idx)  el.classList.add('done');
    if (i === idx) el.classList.add('active');
  });
}

/* ─────────────────────────────
   Progress helpers
───────────────────────────── */
function setProgress(pct, label) {
  progBar.style.width = pct + '%';
  progPct.textContent = pct + '%';
  statusLabel.textContent = label;
  progTrack.setAttribute('aria-valuenow', pct);
}

/* ─────────────────────────────
   Script renderer
───────────────────────────── */
function renderScript(script) {
  if (!script?.scenes?.length) return;
  const title = `<h3 style="font-size:1rem;font-weight:700;color:var(--accent2);margin-bottom:16px">${esc(script.title)}</h3>`;
  const scenes = script.scenes.map((sc, i) => `
    <div class="scene-card">
      <div class="scene-num">Scene ${i + 1}</div>
      <div class="scene-title">${esc(sc.title)}</div>
      <div class="scene-narr">${esc(sc.narration)}</div>
      <div class="scene-meta">
        <span>⏱ ${sc.duration}s</span>
        <span>🖼 ${esc(sc.visual_description.slice(0, 70))}${sc.visual_description.length > 70 ? '…' : ''}</span>
      </div>
    </div>
  `).join('');
  scriptContent.innerHTML = title + scenes;
}

function esc(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ─────────────────────────────
   Script collapse toggle
───────────────────────────── */
document.getElementById('script-toggle').addEventListener('click', function () {
  const expanded = this.getAttribute('aria-expanded') === 'true';
  this.setAttribute('aria-expanded', String(!expanded));
  scriptContent.classList.toggle('collapsed', expanded);
});

/* ─────────────────────────────
   Poll job status
───────────────────────────── */
async function pollJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/video/status/${jobId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    switch (data.status) {
      case 'queued':
        setProgress(5, 'Waiting in queue…');
        break;

      case 'generating_script':
        setStep('generating_script');
        setProgress(data.progress || 20, 'Generating AI script with Claude…');
        break;

      case 'creating_video':
        setStep('creating_video');
        setProgress(data.progress || 55, 'Rendering scenes, narration & transitions…');
        if (data.script && !scriptContent.innerHTML) {
          renderScript(data.script);
          show(progressCard, scriptCard);
        }
        break;

      case 'completed':
        clearInterval(pollTimer);
        setStep('completed');
        setProgress(100, 'Done!');
        statusDot.classList.add('done');
        if (data.script && !scriptContent.innerHTML) renderScript(data.script);

        // Wire up video player
        const videoSrc = data.download_url;
        videoPlayer.src = videoSrc;
        downloadLink.href = videoSrc;

        setTimeout(() => show(resultCard, scriptCard), 600);
        // Haptic feedback on supported devices
        if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
        break;

      case 'failed':
        clearInterval(pollTimer);
        statusDot.classList.add('err');
        errorMsg.textContent = data.error || 'Video generation failed. Please try again.';
        show(errorCard);
        break;
    }
  } catch (err) {
    console.error('Poll error:', err);
  }
}

/* ─────────────────────────────
   Form submission
───────────────────────────── */
form.addEventListener('submit', async e => {
  e.preventDefault();

  const topic = topicEl.value.trim();
  if (!topic) { topicEl.focus(); return; }

  const payload = {
    topic,
    style:       styleInput.value,
    duration:    parseInt(document.getElementById('duration').value, 10),
    color_theme: document.getElementById('theme').value,
    voice_speed: parseFloat(speedInput.value),
  };

  generateBtn.disabled = true;
  generateBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Starting…';

  scriptContent.innerHTML = '';
  statusDot.classList.remove('done', 'err');
  [stepScript, stepVideo, stepDone].forEach(s => s.classList.remove('active', 'done'));
  setProgress(0, 'Queued…');
  show(progressCard);

  try {
    const res = await fetch(`${API_BASE}/video/generate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const { job_id } = await res.json();

    clearInterval(pollTimer);
    pollTimer = setInterval(() => pollJob(job_id), POLL_MS);
    pollJob(job_id);

  } catch (err) {
    errorMsg.textContent = err.message || 'Failed to start video generation.';
    show(errorCard);
  } finally {
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Generate Video';
  }
});

/* ─────────────────────────────
   Share button (Web Share API)
───────────────────────────── */
document.getElementById('share-btn').addEventListener('click', async () => {
  const videoUrl = downloadLink.href;

  if (navigator.share) {
    try {
      await navigator.share({
        title: 'My AI-Generated Video',
        text:  'Check out this video I made with AI Video Creator!',
        url:   window.location.origin,
      });
      return;
    } catch (err) {
      if (err.name === 'AbortError') return; // user cancelled
    }
  }

  // Fallback: copy download URL to clipboard
  try {
    await navigator.clipboard.writeText(videoUrl);
    toast('Download link copied!');
  } catch {
    toast('Share: ' + videoUrl);
  }
});

/* ─────────────────────────────
   New video / retry
───────────────────────────── */
document.getElementById('new-video-btn').addEventListener('click', () => {
  clearInterval(pollTimer);
  videoPlayer.src = '';
  show(formCard);
});

document.getElementById('retry-btn').addEventListener('click', () => {
  clearInterval(pollTimer);
  show(formCard);
});

/* ─────────────────────────────
   QR Code modal
───────────────────────────── */
const qrModal  = document.getElementById('qr-modal');
const qrImg    = document.getElementById('qr-img');
const qrUrlEl  = document.getElementById('qr-url');
const copyBtn  = document.getElementById('copy-url');

document.getElementById('qr-btn').addEventListener('click', openQR);
document.getElementById('qr-close').addEventListener('click', closeQR);

// Close on overlay click (not sheet click)
qrModal.addEventListener('click', e => {
  if (e.target === qrModal) closeQR();
});

// Close on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && !qrModal.classList.contains('hidden')) closeQR();
});

async function openQR() {
  // Try to get the local network URL from backend first
  let url = window.location.origin;
  try {
    const info = await fetch(`${API_BASE}/network-info`).then(r => r.json());
    if (info.ips?.length) {
      url = `http://${info.ips[0]}:${info.port}`;
    }
  } catch {}

  qrUrlEl.textContent = url;
  // Use qrserver.com API — reliable, free, no signup
  qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&margin=10&data=${encodeURIComponent(url)}`;

  qrModal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeQR() {
  qrModal.classList.add('hidden');
  document.body.style.overflow = '';
}

copyBtn.addEventListener('click', async () => {
  const url = qrUrlEl.textContent;
  try {
    await navigator.clipboard.writeText(url);
    copyBtn.textContent = 'Copied!';
    copyBtn.classList.add('copied');
    setTimeout(() => {
      copyBtn.textContent = 'Copy';
      copyBtn.classList.remove('copied');
    }, 2000);
  } catch {
    toast('Copy failed');
  }
});

/* ─────────────────────────────
   Toast helper
───────────────────────────── */
const toastEl = document.getElementById('toast');
let toastTimer = null;

function toast(msg, duration = 2500) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), duration);
}

/* ─────────────────────────────
   Spinner keyframe (for loading btn)
───────────────────────────── */
const spinStyle = document.createElement('style');
spinStyle.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
document.head.appendChild(spinStyle);
