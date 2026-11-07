const board = document.getElementById('board');
const deep = document.getElementById('deep');
const status = document.getElementById('status');

function sevClass(n) {
  if (n >= 8) return 'high';
  if (n >= 6) return 'mid';
  return 'low';
}

function render(pack) {
  board.innerHTML = '';
  deep.innerHTML = '';
  status.textContent = `mode=${pack.mode} · tavily=${pack.tavily_used} · ${pack.cards.length} cards · ${pack.deep_briefs.length} deep`;
  for (const c of pack.cards) {
    const el = document.createElement('article');
    el.className = 'card';
    const hits = (c.market_hits || []).slice(0, 2).map(h => `• ${h.title}`).join('<br/>');
    el.innerHTML = `
      <div class="sev ${sevClass(c.severity)}">${c.severity}</div>
      <div>
        <h2>${c.triage_headline}</h2>
        <div class="sub">${c.ticker} · filed ${c.filed_on} · clock ${c.clock_hours}h · ${c.owner_seat} · ${c.mode}/${c.model_used}</div>
        <div class="why">${c.why_triage}</div>
        ${hits ? `<div class="hits"><strong>Tavily (market only):</strong><br/>${hits}</div>` : ''}
      </div>`;
    board.appendChild(el);
  }
  for (const b of pack.deep_briefs || []) {
    const el = document.createElement('article');
    el.className = 'brief';
    el.innerHTML = `
      <h3>${b.fixture_id} · AC one-liner</h3>
      <p>${b.ac_one_liner}</p>
      <p><strong>Why now:</strong> ${b.why_now}</p>
      <div><strong>ICFR focus</strong><ul>${(b.icfr_focus||[]).map(x=>`<li>${x}</li>`).join('')}</ul></div>
      <div><strong>Next actions</strong><ul>${(b.next_actions||[]).map(x=>`<li>${x}</li>`).join('')}</ul></div>
      <p class="sub">${b.mode} · ${b.model_used}</p>`;
    deep.appendChild(el);
  }
}

async function scan(offline) {
  status.textContent = 'Scanning…';
  const q = new URLSearchParams({ offline: offline ? 'true' : 'false', deep_all: 'true', tavily: 'false' });
  const res = await fetch('/api/scan?' + q.toString());
  const pack = await res.json();
  render(pack);
}

document.getElementById('btn-scan').onclick = () => scan(false);
document.getElementById('btn-offline').onclick = () => scan(true);
