(() => {
  const EVENTS_KEY = 'campusbeacon.events.v1';
  const MARKS_KEY = 'campusbeacon.event-marks.v1';
  const read = key => {
    try { return JSON.parse(localStorage.getItem(key) || '{}'); }
    catch (_) { return {}; }
  };
  const write = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const formatDate = (value, options) => new Date(value).toLocaleString(undefined, options);
  const lists = {
    ongoing: document.getElementById('ongoing-events'),
    upcoming: document.getElementById('upcoming-events'),
    finished: document.getElementById('finished-events')
  };
  const statusLabels = {ongoing:'Ongoing',upcoming:'Upcoming',finished:'Finished'};
  function currentPhase(event) {
    const now = Date.now();
    if (new Date(event.endsAt).getTime() <= now) return 'finished';
    if (new Date(event.startsAt).getTime() <= now) return 'ongoing';
    return 'upcoming';
  }
  const urlParams = new URLSearchParams(window.location.search);
  const search = (urlParams.get('q') || '').toLowerCase();
  const category = urlParams.get('category') || '';

  function appendMarkEditor(parent, eventId, initial='') {
    const editor = make('div', 'event-mark mt-2');
    editor.dataset.eventMark = eventId;
    const label = make('label', 'small text-secondary', 'Add a mark or note');
    const input = make('input', 'form-control form-control-sm mt-1');
    input.maxLength = 240;
    input.placeholder = 'e.g. attended, key takeaway…';
    input.value = initial;
    input.setAttribute('aria-label', 'Add a mark or note to this ongoing event');
    label.append(input);
    const save = make('button', 'btn btn-sm btn-outline-secondary mt-2', 'Save mark');
    save.type = 'button';
    save.dataset.saveMark = '';
    const saved = make('small', 'event-mark-saved d-block mt-1');
    saved.textContent = initial ? 'Mark saved in this browser.' : '';
    editor.append(label, save, saved);
    parent.append(editor);
  }

  function addLocalEventCard(event) {
    if (search && !`${event.title} ${event.description} ${event.venue}`.toLowerCase().includes(search)) return false;
    if (category && event.category !== category) return false;
    const phase = currentPhase(event);
    const list = lists[phase];
    if (!list) return false;
    const col = make('div', 'col-md-6 col-xl-4 event-column');
    col.dataset.localEventId = event.id;
    const card = make('article', 'card event-card h-100');
    const body = make('div', 'card-body');
    const top = make('div', 'd-flex justify-content-between align-items-start gap-2');
    top.append(make('span', 'badge-soft', event.category));
    top.append(make('span', `event-state ${phase}`, statusLabels[phase]));
    body.append(top, make('h3', '', event.title), make('p', '', event.description));
    body.append(make('div', 'small text-secondary', event.venue));
    const starts = new Date(event.startsAt);
    const ends = new Date(event.endsAt);
    const dateText = phase === 'finished'
      ? formatDate(starts, {day:'numeric',month:'short',year:'numeric',hour:'numeric',minute:'2-digit'})
      : phase === 'ongoing'
        ? `Until ${formatDate(ends, {hour:'numeric',minute:'2-digit'})}`
        : formatDate(starts, {weekday:'short',day:'numeric',month:'short',hour:'numeric',minute:'2-digit'});
    body.append(make('div', 'small text-secondary mt-2', dateText));
    card.append(body);
    col.append(card);
    if (phase === 'upcoming') {
      const actions = make('div', 'd-flex align-items-center gap-2 mt-2');
      const register = make('button', 'btn btn-sm btn-primary', 'Register');
      register.type = 'button';
      register.dataset.registerEvent = '';
      register.dataset.eventId = event.id;
      register.dataset.eventTitle = event.title;
      register.dataset.eventCategory = event.category;
      register.dataset.eventVenue = event.venue;
      register.dataset.eventStarts = event.startsAt;
      register.dataset.eventEnds = event.endsAt;
      actions.append(register, make('span', 'small text-secondary', ''));
      actions.lastChild.dataset.registrationFeedback = '';
      actions.lastChild.setAttribute('aria-live', 'polite');
      col.append(actions);
    }
    if (phase === 'ongoing') appendMarkEditor(col, event.id, read(MARKS_KEY)[event.id] || '');
    list.append(col);
    return true;
  }

  function renderLocalEvents() {
    document.querySelectorAll('[data-local-event-id]').forEach(node => node.remove());
    let visible = 0;
    const events = Object.values(read(EVENTS_KEY)).sort((a,b) => a.startsAt.localeCompare(b.startsAt));
    for (const event of events) if (addLocalEventCard(event)) visible += 1;
    for (const [phase, list] of Object.entries(lists)) {
      if (!list) continue;
      const count = document.querySelector(`[data-count-for="${list.id}"]`);
      const total = list.querySelectorAll('.event-column').length;
      if (count) count.textContent = total;
      const section = list.closest('.event-group');
      const empty = section && section.querySelector('.event-empty');
      if (empty) empty.classList.toggle('d-none', total > 0);
    }
    const allEmptyMessage = document.getElementById('no-events-match');
    if (allEmptyMessage && visible) allEmptyMessage.classList.add('d-none');
  }

  const marks = read(MARKS_KEY);
  document.querySelectorAll('[data-event-mark]').forEach(editor => {
    const value = marks[editor.dataset.eventMark] || '';
    const input = editor.querySelector('input');
    const saved = editor.querySelector('.event-mark-saved');
    if (input) input.value = value;
    if (saved && value) saved.textContent = 'Mark saved in this browser.';
  });

  document.addEventListener('click', event => {
    if (event.target.closest('[data-close-event-form]')) {
      document.getElementById('add-event-panel').open = false;
      return;
    }
    const button = event.target.closest('[data-save-mark]');
    if (!button) return;
    const editor = button.closest('[data-event-mark]');
    const marksNow = read(MARKS_KEY);
    const value = editor.querySelector('input').value.trim();
    if (value) marksNow[editor.dataset.eventMark] = value;
    else delete marksNow[editor.dataset.eventMark];
    write(MARKS_KEY, marksNow);
    editor.querySelector('.event-mark-saved').textContent = value ? 'Mark saved in this browser.' : 'Mark cleared.';
  });

  document.getElementById('add-event-form').addEventListener('submit', event => {
    event.preventDefault();
    const feedback = document.getElementById('add-event-feedback');
    const title = document.getElementById('new-event-title').value.trim();
    const categoryValue = document.getElementById('new-event-category').value;
    const venue = document.getElementById('new-event-place').value.trim();
    const description = document.getElementById('new-event-description').value.trim();
    const phase = document.getElementById('new-event-phase').value;
    const startInput = document.getElementById('new-event-start');
    const endInput = document.getElementById('new-event-end');
    let startsAt = new Date(startInput.value);
    const endsAt = new Date(endInput.value);
    const now = new Date();
    if (!title || !venue || !description || Number.isNaN(startsAt.getTime()) || Number.isNaN(endsAt.getTime())) {
      feedback.textContent = 'Fill in the event name, place, description, and both times.';
      return;
    }
    if (endsAt <= startsAt) { feedback.textContent = 'The end time must be after the start time.'; return; }
    if (phase === 'upcoming' && startsAt <= now) { feedback.textContent = 'Choose a future start time for an upcoming event.'; return; }
    if (phase === 'finished' && endsAt >= now) { feedback.textContent = 'Choose a past end time for a finished event.'; return; }
    if (phase === 'ongoing') {
      if (endsAt <= now) { feedback.textContent = 'An ongoing event needs an end time in the future.'; return; }
      startsAt = now;
    }
    const newEvent = {
      id: `local-${Date.now()}`,
      title, category:categoryValue, venue, description, phase,
      startsAt:startsAt.toISOString(), endsAt:endsAt.toISOString()
    };
    const events = read(EVENTS_KEY);
    events[newEvent.id] = newEvent;
    try { write(EVENTS_KEY, events); }
    catch (_) { feedback.textContent = 'This browser could not save the event. Check its storage settings.'; return; }
    event.target.reset();
    feedback.textContent = 'Event saved in this browser.';
    renderLocalEvents();
    window.dispatchEvent(new Event('campusbeacon:events-updated'));
  });

  renderLocalEvents();
  window.dispatchEvent(new Event('campusbeacon:events-updated'));
})();
