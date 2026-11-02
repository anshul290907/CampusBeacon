(() => {
  const root = document.querySelector('[data-site-guide]');
  if (!root) return;
  const toggle = root.querySelector('[data-guide-toggle]');
  const panel = root.querySelector('[data-guide-panel]');
  const messages = root.querySelector('[data-guide-messages]');
  const form = root.querySelector('[data-guide-form]');
  const input = root.querySelector('[data-guide-input]');
  let greetTimer;

  const urls = {
    events: '/events', clubs: '/clubs', notices: '/notices', map: '/map',
    dashboard: '/dashboard', notes: '/notes', login: '/login', home: '/'
  };
  const pageName = location.pathname === '/' ? 'home' : location.pathname.split('/').filter(Boolean)[0];
  const pageCompliments = {
    home: 'You’re in the right place to get started.', login: 'You’re taking a great first step by getting connected.',
    dashboard: 'You’re doing a great job keeping your campus life organized.', events: 'Great choice—there’s always something happening.',
    clubs: 'Finding your people is a wonderful move.', notices: 'Staying informed is a smart habit.', map: 'Exploring campus already? Nice!'
  };
  const greet = () => {
    root.classList.add('greeting-visible');
    clearTimeout(greetTimer);
    greetTimer = setTimeout(() => root.classList.remove('greeting-visible'), 7000);
  };
  setTimeout(greet, 450);
  if (matchMedia('(pointer:fine)').matches) {
    document.addEventListener('mousemove', (event) => {
      const button = toggle.getBoundingClientRect();
      const dx = Math.max(-5, Math.min(5, (event.clientX - (button.left + button.width / 2)) / 55));
      const dy = Math.max(-4, Math.min(4, (event.clientY - (button.top + button.height / 2)) / 65));
      toggle.style.setProperty('--look-x', `${dx}px`);
      toggle.style.setProperty('--look-y', `${dy}px`);
    }, { passive: true });
  }
  toggle.addEventListener('click', () => {
    const open = panel.hidden;
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    root.classList.remove('greeting-visible');
    if (open) { input.focus(); greetTimer && clearTimeout(greetTimer); }
  });
  root.querySelector('[data-guide-close]').addEventListener('click', () => {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  });
  function addMessage(text, who = 'bot') {
    const p = document.createElement('p');
    p.className = `guide-message guide-message-${who}`;
    p.textContent = text;
    messages.append(p);
    messages.scrollTop = messages.scrollHeight;
  }
  function guideAnswer(question) {
    const q = question.toLowerCase();
    let key, title, intro;
    if (/event|workshop|hackathon|calendar/.test(q)) [key, title, intro] = ['events', 'Browse events', 'Open Events to browse upcoming activities and filter the list.'];
    else if (/club|societ|community/.test(q)) [key, title, intro] = ['clubs', 'Explore clubs', 'Open Clubs & societies to discover campus groups.'];
    else if (/notice|deadline|announcement/.test(q)) [key, title, intro] = ['notices', 'Read notices', 'Open Notices for announcements and deadlines.'];
    else if (/map|where is|location|building/.test(q)) [key, title, intro] = ['map', 'Open the campus map', 'The Campus map page shows verified campus places.'];
    else if (/note|remind|personal/.test(q)) [key, title, intro] = ['notes', 'Open your notes', 'Your notes page lets you save personal reminders.'];
    else if (/dashboard|register|saved|my event|my account/.test(q)) [key, title, intro] = ['dashboard', 'Go to your dashboard', 'Your dashboard brings together your registrations, notices, and notes.'];
    else if (/sign in|login|google|account/.test(q)) [key, title, intro] = ['login', 'Sign in', 'Use Continue with Google and your approved college account.'];
    else if (/home|start|welcome/.test(q)) [key, title, intro] = ['home', 'Go to the home page', 'The home page is a good place to start exploring CampusBeacon.'];
    else return 'I can help you find events, clubs, notices, the campus map, your dashboard, or notes. Which one would you like?';
    const a = document.createElement('a');
    a.href = urls[key]; a.textContent = title;
    const p = document.createElement('p'); p.className = 'guide-message guide-message-bot';
    p.append(document.createTextNode(`${intro} ${pageCompliments[pageName] || 'You’re doing great exploring CampusBeacon.'} `), a);
    messages.append(p); messages.scrollTop = messages.scrollHeight;
    return null;
  }
  function submit(question) {
    const clean = question.trim();
    if (!clean) return;
    addMessage(clean, 'user');
    const answer = guideAnswer(clean);
    if (answer) addMessage(answer);
  }
  form.addEventListener('submit', (event) => {
    event.preventDefault(); submit(input.value); input.value = '';
  });
  root.querySelectorAll('[data-guide-question]').forEach(button => button.addEventListener('click', () => submit(button.dataset.guideQuestion)));
})();
