(() => {
  const MARKS_KEY = 'campusbeacon.event-marks.v1';
  const readMarks = () => {
    try { return JSON.parse(localStorage.getItem(MARKS_KEY) || '{}'); }
    catch (_) { return {}; }
  };
  const saveMarks = marks => localStorage.setItem(MARKS_KEY, JSON.stringify(marks));

  document.querySelectorAll('[data-event-mark]').forEach(editor => {
    const value = readMarks()[editor.dataset.eventMark] || '';
    const input = editor.querySelector('input');
    const saved = editor.querySelector('.event-mark-saved');
    if (input) input.value = value;
    if (saved && value) saved.textContent = 'Mark saved in this browser.';
  });

  document.addEventListener('click', event => {
    if (event.target.closest('[data-close-event-form]')) {
      const panel = document.getElementById('add-event-panel');
      if (panel) panel.open = false;
      return;
    }
    const button = event.target.closest('[data-save-mark]');
    if (!button) return;
    const editor = button.closest('[data-event-mark]');
    const marks = readMarks();
    const value = editor.querySelector('input').value.trim();
    if (value) marks[editor.dataset.eventMark] = value;
    else delete marks[editor.dataset.eventMark];
    saveMarks(marks);
    editor.querySelector('.event-mark-saved').textContent = value ? 'Mark saved in this browser.' : 'Mark cleared.';
  });

  window.dispatchEvent(new Event('campusbeacon:events-updated'));
})();
