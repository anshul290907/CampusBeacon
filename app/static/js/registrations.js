(() => {
  const TOKEN_KEY = 'campusbeacon.registration-key.v1';
  const LOCAL_KEY = 'campusbeacon.local-registrations.v1';
  const LEGACY_KEY = 'campusbeacon.registrations.v1';
  const dbRegistrations = new Map();
  const readObject = key => {
    try { const value=JSON.parse(localStorage.getItem(key)||'{}'); return value&&typeof value==='object'&&!Array.isArray(value)?value:{}; }
    catch (_) { return {}; }
  };
  const writeObject = (key,value) => localStorage.setItem(key,JSON.stringify(value));
  const readLocalRegistrations = () => ({...readObject(LEGACY_KEY),...readObject(LOCAL_KEY)});
  const setText = (node,value) => { node.textContent=String(value||''); return node; };
  function getKey() {
    let key=localStorage.getItem(TOKEN_KEY)||'';
    if (/^[a-f0-9]{64}$/i.test(key)) return key;
    if (!window.crypto || !window.crypto.getRandomValues) throw new Error('This browser cannot create a secure registration key.');
    const bytes=window.crypto.getRandomValues(new Uint8Array(32));
    key=Array.from(bytes,value=>value.toString(16).padStart(2,'0')).join('');
    localStorage.setItem(TOKEN_KEY,key);
    return key;
  }
  async function request(url,method='GET',key=getKey()) {
    const headers={'X-CampusBeacon-Registration-Key':key};
    const options={method,headers};
    if (method==='POST') { headers['Content-Type']='application/json'; options.body='{}'; }
    const response=await fetch(url,options);
    let data={};
    try { data=await response.json(); } catch (_) { /* The caller handles a generic error. */ }
    return {response,data};
  }
  async function importPreviousRegistrations(key) {
    const legacy=readObject(LEGACY_KEY), local=readObject(LOCAL_KEY);
    let changed=false;
    for (const [id,item] of Object.entries(legacy)) {
      if (!/^\d+$/.test(String(id))) { local[id]=item; delete legacy[id]; changed=true; continue; }
      try {
        const {response}=await request(`/api/events/${encodeURIComponent(id)}/registrations`,'POST',key);
        if (response.ok) { delete legacy[id]; changed=true; }
      } catch (_) { /* Keep the old local record and retry next visit. */ }
    }
    if (changed) { writeObject(LEGACY_KEY,legacy); writeObject(LOCAL_KEY,local); }
  }
  function updateButtons() {
    const local=readLocalRegistrations();
    document.querySelectorAll('[data-register-event]').forEach(button=>{
      const id=String(button.dataset.eventId||'');
      const registered=id.startsWith('local-')?Boolean(local[id]):dbRegistrations.has(id);
      button.textContent=registered?'✓ Registered':(button.closest('.event-column')?'Register':'Register for event');
      button.disabled=registered;
      button.classList.toggle('btn-primary',!registered);
      button.classList.toggle('btn-success',registered);
    });
  }
  function makeCard(item,registrationType='database') {
    const isLocal=registrationType!=='database';
    const column=document.createElement('div'); column.className='col-md-6 col-xl-4';
    const card=document.createElement('article'); card.className='registration-card h-100';
    const category=setText(document.createElement('span'),item.category||'Event'); category.className='badge-soft'; card.append(category);
    const title=document.createElement(/^\d+$/.test(String(item.id))?'a':'h2'); title.className='registration-title'; setText(title,item.title||'Campus event');
    if (title.tagName==='A') title.href=`/events/${encodeURIComponent(item.id)}`;
    card.append(title);
    const date=new Date(item.startsAt),when=document.createElement('p'); when.className='small text-secondary mb-1';
    setText(when,Number.isNaN(date.getTime())?'':date.toLocaleString(undefined,{weekday:'short',day:'numeric',month:'short',hour:'numeric',minute:'2-digit'})); card.append(when);
    const venue=document.createElement('p'); venue.className='small text-secondary'; setText(venue,item.venue||''); card.append(venue);
    if (isLocal) { const note=document.createElement('p'); note.className='small text-secondary'; setText(note,'Saved locally; this event is not in the database.'); card.append(note); }
    const remove=document.createElement('button'); remove.type='button'; remove.className='btn btn-sm btn-outline-secondary'; remove.dataset.removeRegistration=String(item.id); remove.dataset.registrationType=registrationType; setText(remove,'Remove registration'); card.append(remove);
    column.append(card); return column;
  }
  function renderRegistrations() {
    const list=document.getElementById('registration-list'); if (!list) return;
    list.replaceChildren();
    const dbItems=Array.from(dbRegistrations.values());
    const localItems=[
      ...Object.values(readObject(LOCAL_KEY)).map(item=>({...item,_registrationType:'local'})),
      ...Object.values(readObject(LEGACY_KEY)).map(item=>({...item,_registrationType:'legacy'}))
    ];
    for (const item of [...dbItems.map(item=>({...item,_registrationType:'database'})),...localItems].sort((a,b)=>String(a.startsAt).localeCompare(String(b.startsAt)))) list.append(makeCard(item,item._registrationType));
    const empty=document.getElementById('registrations-empty');
    if (empty) empty.classList.toggle('d-none',dbItems.length+localItems.length>0);
  }
  async function refresh() {
    const feedback=document.getElementById('registration-page-feedback');
    try {
      const key=getKey();
      await importPreviousRegistrations(key);
      const {response,data}=await request('/api/registrations','GET',key);
      if (!response.ok) throw new Error(data.error||'Could not load registrations from the database.');
      dbRegistrations.clear();
      for (const item of data.registrations||[]) dbRegistrations.set(String(item.id),item);
      if (feedback) feedback.textContent='Connected to the CampusBeacon database.';
    } catch (error) {
      if (feedback) feedback.textContent=error.message||'Could not connect to the database.';
    }
    updateButtons(); renderRegistrations();
  }
  document.addEventListener('click',async event=>{
    const button=event.target.closest('[data-register-event]');
    if (button&&!button.disabled) {
      const id=String(button.dataset.eventId||''),feedback=button.parentElement.querySelector('[data-registration-feedback]');
      button.disabled=true;
      try {
        if (id.startsWith('local-')) {
          const local=readObject(LOCAL_KEY);
          local[id]={id,title:button.dataset.eventTitle,category:button.dataset.eventCategory,venue:button.dataset.eventVenue,startsAt:button.dataset.eventStarts,endsAt:button.dataset.eventEnds};
          writeObject(LOCAL_KEY,local);
          if (feedback) feedback.textContent='Saved with this browser-only event.';
        } else {
          const {response,data}=await request(`/api/events/${encodeURIComponent(id)}/registrations`,'POST');
          if (!response.ok) throw new Error(data.error||'Could not save registration.');
          if (feedback) feedback.textContent='Registration saved to the database.';
          await refresh();
        }
        updateButtons(); renderRegistrations();
      } catch (error) {
        button.disabled=false;
        if (feedback) feedback.textContent=error.message||'Could not save registration.';
      }
      return;
    }
    const remove=event.target.closest('[data-remove-registration]'); if (!remove) return;
    remove.disabled=true;
    try {
      if (remove.dataset.registrationType==='local' || remove.dataset.registrationType==='legacy') {
        const storageKey=remove.dataset.registrationType==='local'?LOCAL_KEY:LEGACY_KEY;
        const local=readObject(storageKey); delete local[remove.dataset.removeRegistration]; writeObject(storageKey,local);
      } else {
        const {response,data}=await request(`/api/events/${encodeURIComponent(remove.dataset.removeRegistration)}/registrations`,'DELETE');
        if (!response.ok) throw new Error(data.error||'Could not remove registration.');
        dbRegistrations.delete(String(remove.dataset.removeRegistration));
      }
      updateButtons(); renderRegistrations();
    } catch (error) {
      remove.disabled=false;
      const feedback=document.getElementById('registration-page-feedback');
      if (feedback) feedback.textContent=error.message||'Could not remove registration.';
    }
  });
  window.addEventListener('campusbeacon:events-updated',updateButtons);
  updateButtons(); renderRegistrations();
  refresh();
})();
