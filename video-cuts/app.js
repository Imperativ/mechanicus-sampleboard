'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const ui = { pads: $('pads'), status: $('status'), search: $('search'), character: $('character'), group: $('group'), source: $('source'), volume: $('volume'), overlap: $('overlap') };
  const manifest = window.SAMPLEBOARD;
  const records = [];
  let visible = [], frame = 0;
  const text = value => value == null ? '' : String(value);
  const el = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = text(content);
    return node;
  };
  const status = (message, error = false) => {
    ui.status.textContent = message;
    ui.status.parentElement.classList.toggle('error', error);
  };
  const duration = seconds => {
    const n = Number(seconds);
    if (!Number.isFinite(n) || n < 0) return '–:––';
    return `${Math.floor(n / 60)}:${String(Math.floor(n % 60)).padStart(2, '0')}`;
  };
  const localPath = value => {
    if (typeof value !== 'string' || !value.trim() || /^[a-z][a-z0-9+.-]*:/i.test(value.trim()) || /^[\\/]/.test(value.trim()) || /[\x00-\x1f\\]/.test(value)) return '';
    return value;
  };
  const sourceURL = value => {
    try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : ''; } catch { return ''; }
  };
  function reset(record) {
    record.token++;
    record.active = false;
    record.audio.pause();
    try { record.audio.currentTime = 0; } catch { /* Unloaded media may not be seekable. */ }
    record.card.classList.remove('playing');
    record.button.setAttribute('aria-pressed', 'false');
    record.label.textContent = '▶ Abspielen';
    record.fill.style.width = '0%';
    record.time.textContent = duration(record.sample.duration);
  }
  function stopAll(announce = true) {
    records.forEach(reset);
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
    if (announce) status('Alle Wiedergaben gestoppt.');
  }
  function tick() {
    frame = 0;
    records.forEach(record => {
      if (!record.active) return;
      const total = record.audio.duration;
      const position = record.audio.currentTime;
      record.fill.style.width = `${Number.isFinite(total) && total > 0 ? Math.min(100, position / total * 100) : 0}%`;
      record.time.textContent = `${duration(position)} / ${duration(Number.isFinite(total) ? total : record.sample.duration)}`;
    });
    if (records.some(record => record.active)) frame = requestAnimationFrame(tick);
  }
  function fail(record, reason) {
    reset(record);
    record.card.classList.add('failed');
    record.label.textContent = '↻ Erneut versuchen';
    status(`„${text(record.sample.title)}“: ${reason} Prüfen Sie die Audiodatei und ihren relativen Pfad im Manifest. Keine Ersatzsounds.`, true);
  }
  async function toggle(record) {
    if (record.active) { reset(record); status(`„${text(record.sample.title)}“ gestoppt.`); return; }
    if (!record.path) { fail(record, 'Kein gültiger lokaler WAV-/MP3-Pfad vorhanden.'); return; }
    if (!ui.overlap.checked) stopAll(false);
    record.card.classList.remove('failed');
    record.audio.volume = Number(ui.volume.value) / 100;
    record.active = true;
    const token = ++record.token;
    record.card.classList.add('playing');
    record.button.setAttribute('aria-pressed', 'true');
    record.label.textContent = '■ Stoppen';
    status(`Lade „${text(record.sample.title)}“ …`);
    if (!frame) frame = requestAnimationFrame(tick);
    try {
      await record.audio.play();
      if (token !== record.token) return;
      status(`Wiedergabe: ${text(record.sample.title)}${record.audio.loop ? ' · Loop' : ''}`);
    } catch (error) {
      if (token !== record.token) return;
      fail(record, error.name === 'NotAllowedError' ? 'Wiedergabe vom Browser blockiert; Pad direkt anklicken.' : 'Audiodatei nicht lesbar oder Format nicht unterstützt.');
    }
  }
  function waveform(values) {
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'waveform');
    svg.setAttribute('viewBox', '0 0 240 34');
    svg.setAttribute('aria-hidden', 'true');
    if (!Array.isArray(values) || !values.length) return svg;
    const count = Math.min(60, values.length), step = 240 / count;
    for (let i = 0; i < count; i++) {
      const raw = Number(values[Math.floor(i * values.length / count)]);
      const amplitude = Number.isFinite(raw) ? Math.max(0, Math.min(1, raw)) : 0;
      const height = Math.max(1, amplitude * 32);
      const bar = document.createElementNS(ns, 'rect');
      bar.setAttribute('x', String(i * step)); bar.setAttribute('y', String((34 - height) / 2));
      bar.setAttribute('width', String(Math.max(1, step - 2))); bar.setAttribute('height', String(height));
      bar.setAttribute('fill', 'currentColor'); svg.append(bar);
    }
    return svg;
  }
  window.boardDebug = {
    get state() { return !manifest || !Array.isArray(manifest.samples) ? 'missing-manifest' : records.some(r => r.active) ? 'playing' : 'idle'; },
    get totalCount() { return records.length; },
    get visibleCount() { return visible.length; },
    get activeCount() { return records.filter(r => r.active).length; },
    get activeIds() { return records.filter(r => r.active).map(r => r.sample.id); },
    get volume() { return Number(ui.volume.value) / 100; },
    get overlap() { return ui.overlap.checked; },
    stopAll
  };
  $('stop-all').addEventListener('click', () => stopAll());
  ui.volume.addEventListener('input', () => {
    $('volume-value').textContent = `${ui.volume.value} %`;
    records.forEach(r => { r.audio.volume = Number(ui.volume.value) / 100; });
  });
  ui.overlap.addEventListener('change', () => {
    if (!ui.overlap.checked) stopAll(false);
    status(ui.overlap.checked ? 'Überlagerung aktiviert. Mehrere Clips können gleichzeitig laufen.' : 'Einzelwiedergabe aktiviert.');
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') { stopAll(); return; }
    if (event.repeat || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.isComposing) return;
    if (event.target.closest('input, select, textarea, button, a, [contenteditable]')) return;
    if (/^[1-9]$/.test(event.key)) {
      const record = visible[Number(event.key) - 1];
      if (record) { event.preventDefault(); toggle(record); }
    }
  });
  window.addEventListener('pagehide', () => stopAll(false));
  if (!manifest || !Array.isArray(manifest.samples)) {
    status('Manifest fehlt oder ist ungültig. samples.js muss neben index.html liegen und window.SAMPLEBOARD mit einem samples-Array definieren. Keine Ersatzsounds verfügbar.', true);
    $('empty').hidden = false;
    $('empty').textContent = 'Kein Audioarchiv geladen. Bitte die echte samples.js und ihre Audiodateien bereitstellen.';
    return;
  }
  if (manifest.title) { $('board-title').textContent = text(manifest.title); document.title = text(manifest.title); }
  const sources = Array.isArray(manifest.sources) ? manifest.sources.filter(s => s && typeof s === 'object') : [];
  const sourceMap = new Map(sources.map(s => [text(s.id), s]));
  sources.forEach(source => {
    const item = el('li');
    const url = sourceURL(source.url);
    const title = el(url ? 'a' : 'span', '', source.title || source.id || 'Unbenannte Quelle');
    if (url) { title.href = url; title.target = '_blank'; title.rel = 'noopener noreferrer'; }
    item.append(title, el('span', 'source-description', source.description || 'Herkunft laut Manifest; nicht unabhängig authentifiziert.'));
    $('sources').append(item);
  });
  if (!sources.length) $('sources').append(el('li', '', 'Keine Quellenangaben im Manifest vorhanden.'));
  const processing = manifest.processing;
  $('processing-note').textContent = processing ? `${text(processing.format)} · Spitzenpegel höchstens ${text(processing.peakCeilingDbfs)} dBFS · ${text(processing.fadeMilliseconds)} ms Fades. Alle Schnittparameter und Quellenzeiten: manifest.json.` : 'Details zur Verarbeitung sind im Manifest nicht angegeben.';
  manifest.samples.filter(s => s && typeof s === 'object').forEach(sample => {
    const card = el('article', 'pad');
    const button = el('button', 'pad-main'); button.type = 'button';
    button.setAttribute('aria-label', `${text(sample.title || 'Unbenannter Clip')} abspielen / stoppen`);
    button.setAttribute('aria-pressed', 'false');
    const top = el('span', 'pad-top');
    const shortcut = el('kbd'); shortcut.hidden = true;
    top.append(el('span', 'character', sample.character || 'Charakter nicht angegeben'), shortcut);
    const source = sourceMap.get(text(sample.sourceId));
    const metadata = [text(sample.group), text(source ? source.title || source.id : sample.sourceId)].filter(Boolean).join(' · ');
    const transport = el('span', 'pad-transport');
    const label = el('span', 'play-label', '▶ Abspielen'), time = el('span', '', duration(sample.duration));
    transport.append(label, time);
    button.append(top, el('span', 'pad-title', sample.title || 'Unbenannter Clip'), el('span', 'pad-meta', metadata), waveform(sample.waveform), transport);
    const track = el('div', 'progress-track'), fill = el('div', 'progress-fill'); track.setAttribute('aria-hidden', 'true'); track.append(fill);
    const actions = el('div', 'pad-actions'), loopLabel = el('label', 'loop-label'), loop = el('input');
    loop.type = 'checkbox'; loop.setAttribute('aria-label', `Loop für ${text(sample.title || 'Clip')}`);
    loopLabel.append(loop, document.createTextNode('Loop'));
    const downloads = el('div', 'downloads');
    for (const format of ['wav', 'mp3']) {
      const path = localPath(sample[format]);
      const link = el(path ? 'a' : 'span', path ? '' : 'download-unavailable', format.toUpperCase());
      if (path) { link.href = path; link.download = ''; link.setAttribute('aria-label', `${text(sample.title || 'Clip')} als ${format.toUpperCase()} herunterladen`); }
      else link.title = `${format.toUpperCase()} nicht vorhanden`;
      downloads.append(link);
    }
    const origin = sourceURL(sample.sourceUrl || (source && source.url));
    if (origin) {
      const link = el('a', '', 'Quelle');
      const url = new URL(origin);
      if (url.hostname.endsWith('youtube.com') && Number.isFinite(sample.start)) url.searchParams.set('t', String(Math.floor(sample.start)));
      link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.setAttribute('aria-label', `Quelle für ${text(sample.title || 'Clip')}`);
      downloads.append(link);
    }
    card.dataset.sampleId = text(sample.id);
    button.title = text(sample.verification);
    actions.append(loopLabel, downloads); card.append(button, track, actions);
    const wav = localPath(sample.wav), mp3 = localPath(sample.mp3);
    const audio = new Audio(); audio.preload = 'none'; audio.volume = .35;
    const path = wav && audio.canPlayType('audio/wav') ? wav : mp3 || wav;
    if (path) audio.src = path;
    const record = { sample, card, button, shortcut, label, time, fill, audio, path, active: false, token: 0 };
    records.push(record);
    button.addEventListener('click', () => toggle(record));
    loop.addEventListener('change', () => { audio.loop = loop.checked; });
    audio.addEventListener('ended', () => { reset(record); status(`„${text(sample.title)}“ beendet.`); });
    audio.addEventListener('pause', () => {
      if (record.active && audio.paused && !audio.ended) { reset(record); status(`„${text(sample.title)}“ pausiert / gestoppt.`); }
    });
    audio.addEventListener('error', () => {
      const code = audio.error ? audio.error.code : 0;
      fail(record, code === 4 ? 'Audioformat oder Datei nicht unterstützt.' : code === 3 ? 'Audio konnte nicht dekodiert werden.' : 'Audiodatei konnte nicht geladen werden.');
    });
  });
  function options(select, values) {
    [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'de')).forEach(value => {
      const option = el('option', '', value); option.value = value; select.append(option);
    });
  }
  options(ui.character, records.map(r => text(r.sample.character)));
  options(ui.group, records.map(r => text(r.sample.group)));
  const usedSources = [...new Set(records.map(r => text(r.sample.sourceId)).filter(Boolean))];
  usedSources.forEach(id => { const source = sourceMap.get(id); const option = el('option', '', source ? source.title || id : id); option.value = id; ui.source.append(option); });
  function filter() {
    const query = ui.search.value.trim().toLocaleLowerCase('de');
    visible = records.filter(record => {
      const s = record.sample, source = sourceMap.get(text(s.sourceId));
      const haystack = [s.title, s.character, s.group, s.sourceId, source && source.title].map(text).join(' ').toLocaleLowerCase('de');
      return (!ui.character.value || text(s.character) === ui.character.value) && (!ui.group.value || text(s.group) === ui.group.value) && (!ui.source.value || text(s.sourceId) === ui.source.value) && (!query || haystack.includes(query));
    });
    // Hidden pads must not leave invisible audio running.
    records.forEach(record => {
      const index = visible.indexOf(record);
      record.card.hidden = index < 0;
      record.shortcut.hidden = index < 0 || index > 8;
      record.shortcut.textContent = index >= 0 && index < 9 ? String(index + 1) : '';
      if (index >= 0 && index < 9) record.button.setAttribute('aria-keyshortcuts', String(index + 1));
      else record.button.removeAttribute('aria-keyshortcuts');
      if (index < 0 && record.active) reset(record);
    });
    const fragment = document.createDocumentFragment(); records.forEach(r => fragment.append(r.card)); ui.pads.append(fragment);
    $('visible-count').textContent = `// ${visible.length} sichtbar`;
    $('empty').hidden = visible.length > 0;
  }
  ui.search.addEventListener('input', filter);
  [ui.character, ui.group, ui.source].forEach(select => select.addEventListener('change', filter));
  $('total-count').textContent = String(records.length);
  filter();
  status(records.length ? `Archiv bereit: ${records.length} Samples. Master-Pegel 35 %. Keine Wiedergabe ohne Ihre Aktion.` : 'Manifest geladen, aber keine Samples vorhanden.');
})();
