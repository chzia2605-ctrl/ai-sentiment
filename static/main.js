const analyzeBtn = document.getElementById('analyze');
const textEl = document.getElementById('text');
const resultEl = document.getElementById('result');
const jsonEl = document.getElementById('json');

const iconEl = () => document.getElementById('icon');
const labelEl = () => document.getElementById('label');
const scoreEl = () => document.getElementById('score');
const explanationEl = () => document.getElementById('explanation');

// Fetch server status to show if Gemini is configured (no secrets exposed)
async function initStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const s = await res.json();
    const useEl = document.getElementById('useGemini');
    const lbl = document.getElementById('useGeminiLabel');
    useEl.checked = !!s.gemini_enabled;
    if (s.gemini_enabled) {
      lbl.textContent = `Gemini configured (${s.mode}${s.model ? ' — ' + s.model : ''})`;
      if (s.require_gemini) lbl.textContent += ' — required';
    } else {
      lbl.textContent = s.require_gemini ? 'Gemini required (not configured)' : 'Use Gemini (not configured)';
    }
  } catch (e) {
    // silently ignore — status is optional
    console.warn('Could not fetch status', e);
  }
}

// Initialize on load
initStatus();

function setIconSvg(sentiment) {
  const svg = document.getElementById('icon-svg');
  if (!svg) return;
  if (sentiment === 'positive') {
    svg.innerHTML = `
      <circle cx="12" cy="12" r="10" fill="#ecfdf5"/>
      <path d="M8 13s1.5 2 4 2 4-2 4-2" stroke="#059669" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      <path d="M9 10h.01M15 10h.01" stroke="#059669" stroke-width="1.5" stroke-linecap="round" />
    `;
  } else if (sentiment === 'neutral') {
    svg.innerHTML = `
      <circle cx="12" cy="12" r="10" fill="#f8fafc"/>
      <path d="M9 14h6" stroke="#6b7280" stroke-width="1.5" stroke-linecap="round" />
      <path d="M9 10h.01M15 10h.01" stroke="#6b7280" stroke-width="1.5" stroke-linecap="round" />
    `;
  } else if (sentiment === 'negative') {
    svg.innerHTML = `
      <circle cx="12" cy="12" r="10" fill="#fff1f2"/>
      <path d="M8 16s1.5-2 4-2 4 2 4 2" stroke="#dc2626" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      <path d="M9 10h.01M15 10h.01" stroke="#dc2626" stroke-width="1.5" stroke-linecap="round" />
    `;
  } else {
    svg.innerHTML = `
      <circle cx="12" cy="12" r="10" fill="#eef2ff"/>
      <path d="M11 7h2v6h-2zM11 14h2v2h-2z" fill="#1e293b"/>
    `;
  }
}

function burstConfetti() {
  const container = document.getElementById('confetti-container');
  if (!container) return;
  const colors = ['#10b981','#60a5fa','#7c3aed','#facc15'];
  const w = container.offsetWidth || 300;
  const count = 18; // gentler
  for (let i=0;i<count;i++){
    const el = document.createElement('div');
    el.className = 'confetti-piece';
    el.style.left = Math.floor(Math.random()*w) + 'px';
    el.style.background = colors[Math.floor(Math.random()*colors.length)];
    el.style.transform = `rotate(${Math.floor(Math.random()*360)}deg)`;
    container.appendChild(el);
    setTimeout(()=> el.remove(), 1400);
  }
}

function renderResult(data) {
  const card = document.querySelector('.result-card');
  card.classList.add('show');
  resultEl.classList.remove('hidden');

  // Handle errors
  if (data && data.error) {
    setIconSvg('unknown');
    labelEl().textContent = 'Error';
    scoreEl().textContent = '—';
    explanationEl().textContent = data.error;
    jsonEl.textContent = JSON.stringify(data, null, 2);
    card.className = 'result-card unknown show';
    enableActions(false);
    return;
  }

  const sentiment = (data && data.sentiment) ? String(data.sentiment).toLowerCase() : '';
  const score = (data && typeof data.score === 'number') ? data.score : null;
  const explanation = (data && data.explanation) ? data.explanation : JSON.stringify(data);

  const info = {
    positive: { class: 'positive', label: 'Positive' },
    neutral: { class: 'neutral', label: 'Neutral' },
    negative: { class: 'negative', label: 'Negative' }
  }[sentiment] || { class: 'unknown', label: (sentiment || 'Unknown') };

  setIconSvg(sentiment);
  labelEl().textContent = info.label;
  card.className = 'result-card ' + info.class + ' show';

  scoreEl().textContent = (score !== null) ? Math.round(score * 100) + '%' : '—';
  explanationEl().textContent = explanation;
  jsonEl.textContent = JSON.stringify(data, null, 2);

  // Enable copy/share
  enableActions(true);

  // Positive -> confetti
  if (sentiment === 'positive') {
    burstConfetti();
  }
}

function enableActions(enable){
  const copyBtn = document.getElementById('copyBtn');
  const shareBtn = document.getElementById('shareBtn');
  if(copyBtn) copyBtn.disabled = !enable;
  if(shareBtn) shareBtn.disabled = !enable;
}

// Copy & share handlers
function setupActions(){
  const copyBtn = document.getElementById('copyBtn');
  const shareBtn = document.getElementById('shareBtn');
  if(copyBtn) copyBtn.addEventListener('click', async ()=>{
    const text = `${labelEl().textContent} — ${scoreEl().textContent}\n${explanationEl().textContent}`;
    try { await navigator.clipboard.writeText(text); alert('Result copied to clipboard'); }
    catch(e){ alert('Copy failed'); }
  });

  if(shareBtn) shareBtn.addEventListener('click', async ()=>{
    const text = `${labelEl().textContent} — ${scoreEl().textContent}\n${explanationEl().textContent}`;
    if (navigator.share){
      try{ await navigator.share({ title: 'Sentiment result', text }); }
      catch(e){ /* user cancelled */ }
    } else {
      try { await navigator.clipboard.writeText(text); alert('No sharing available; copied to clipboard instead'); }
      catch(e){ alert('Share/copy failed'); }
    }
  });
  // disable by default until a result
  enableActions(false);
}

// Initialize actions
setupActions();

analyzeBtn.addEventListener('click', async () => {
  const text = textEl.value.trim();
  if (!text) return alert('Please enter some text to analyze.');
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = 'Analyzing...';

  try {
    const res = await fetch('/api/sentiment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    renderResult(data);
  } catch (err) {
    alert('Request failed: ' + err);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze Sentiment';
  }
});