'use strict';

const API_BASE = '/api';
const POLL_MS  = 2500;

// DOM refs
const formCard     = document.getElementById('form-card');
const progressCard = document.getElementById('progress-card');
const scriptCard   = document.getElementById('script-card');
const resultCard   = document.getElementById('result-card');
const errorCard    = document.getElementById('error-card');

const form         = document.getElementById('video-form');
const topicEl      = document.getElementById('topic');
const charCount    = document.getElementById('char-count');
const generateBtn  = document.getElementById('generate-btn');

const statusDot    = document.getElementById('status-dot');
const statusLabel  = document.getElementById('status-label');
const progressBar  = document.getElementById('progress-bar');
const progressPct  = document.getElementById('progress-pct');

const stepScript   = document.getElementById('step-script');
const stepVideo    = document.getElementById('step-video');
const stepDone     = document.getElementById('step-done');

const scriptContent = document.getElementById('script-content');
const downloadLink  = document.getElementById('download-link');
const errorMsg      = document.getElementById('error-msg');

let pollTimer = null;

// ── Char counter ──
topicEl.addEventListener('input', () => {
  charCount.textContent = topicEl.value.length;
});

// ── Helpers ──
function show(...cards) {
  [formCard, progressCard, scriptCard, resultCard, errorCard].forEach(c => c.classList.add('hidden'));
  cards.forEach(c => c.classList.remove('hidden'));
}

function setStep(active) {
  [stepScript, stepVideo, stepDone].forEach(s => {
    s.classList.remove('active', 'done');
  });
  const steps = { generating_script: stepScript, creating_video: stepVideo, completed: stepDone };
  const order = ['generating_script', 'creating_video', 'completed'];
  const idx   = order.indexOf(active);
  order.forEach((key, i) => {
    const el = steps[key];
    if (!el) return;
    if (i < idx)  el.classList.add('done');
    if (i === idx) el.classList.add('active');
  });
}

function updateProgress(pct, label) {
  progressBar.style.width = pct + '%';
  progressPct.textContent  = pct + '%';
  statusLabel.textContent  = label;
}

function renderScript(script) {
  if (!script || !script.scenes) return;
  const html = script.scenes.map((sc, i) => `
    <div class="scene-card">
      <div class="scene-num">Scene ${i + 1}</div>
      <div class="scene-title">${escHtml(sc.title)}</div>
      <div class="scene-narration">${escHtml(sc.narration)}</div>
      <div class="scene-meta">
        <span>&#9201; ${sc.duration}s</span>
        <span>&#127760; ${escHtml(sc.visual_description.slice(0,60))}${sc.visual_description.length > 60 ? '…' : ''}</span>
      </div>
    </div>
  `).join('');
  scriptContent.innerHTML = `<h3 style="margin-bottom:16px;color:var(--accent2)">${escHtml(script.title)}</h3>` + html;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

// ── Poll job ──
async function pollJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/video/status/${jobId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    switch (data.status) {
      case 'queued':
        updateProgress(5, 'Waiting in queue…');
        break;

      case 'generating_script':
        setStep('generating_script');
        updateProgress(data.progress || 20, 'Generating AI script with Claude…');
        break;

      case 'creating_video':
        setStep('creating_video');
        updateProgress(data.progress || 50, 'Rendering scenes, narration & transitions…');
        if (data.script) {
          renderScript(data.script);
          show(progressCard, scriptCard);
        }
        break;

      case 'completed':
        clearInterval(pollTimer);
        setStep('completed');
        updateProgress(100, 'Done!');
        statusDot.classList.add('done');
        if (data.script && !scriptContent.innerHTML) renderScript(data.script);

        downloadLink.href = data.download_url;
        downloadLink.setAttribute('download', 'ai_generated_video.mp4');
        setTimeout(() => show(resultCard, scriptCard), 600);
        break;

      case 'failed':
        clearInterval(pollTimer);
        statusDot.classList.add('err');
        errorMsg.textContent = data.error || 'Video generation failed.';
        show(errorCard);
        break;
    }
  } catch (err) {
    console.error('Poll error:', err);
  }
}

// ── Submit ──
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const topic = topicEl.value.trim();
  if (!topic) {
    topicEl.focus();
    return;
  }

  const payload = {
    topic,
    style:       document.getElementById('style').value,
    duration:    parseInt(document.getElementById('duration').value, 10),
    color_theme: document.getElementById('theme').value,
    voice_speed: parseFloat(document.getElementById('speed').value),
  };

  generateBtn.disabled = true;
  generateBtn.innerHTML = '<span class="btn-icon">&#8987;</span> Starting…';

  // Reset state
  scriptContent.innerHTML = '';
  statusDot.classList.remove('done', 'err');
  [stepScript, stepVideo, stepDone].forEach(s => s.classList.remove('active','done'));
  updateProgress(0, 'Queued…');
  show(progressCard);

  try {
    const res = await fetch(`${API_BASE}/video/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const { job_id } = await res.json();

    // Start polling
    clearInterval(pollTimer);
    pollTimer = setInterval(() => pollJob(job_id), POLL_MS);
    pollJob(job_id);

  } catch (err) {
    errorMsg.textContent = err.message || 'Failed to start video generation.';
    show(errorCard);
  } finally {
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<span class="btn-icon">&#9889;</span> Generate Video';
  }
});

// ── New video / retry ──
document.getElementById('new-video-btn').addEventListener('click', () => {
  clearInterval(pollTimer);
  show(formCard);
});
document.getElementById('retry-btn').addEventListener('click', () => {
  clearInterval(pollTimer);
  show(formCard);
});
