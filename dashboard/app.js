let csrf='',state=null,current=null,polling=false;
let currentSession=null,sessionFilter='all',isRawSession=false;
const $=s=>document.querySelector(s),escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(text){$('#toast').textContent=text;$('#toast').classList.remove('hidden');setTimeout(()=>$('#toast').classList.add('hidden'),6000)}
async function api(path,data){const r=await fetch(path,{method:data===undefined?'GET':'POST',headers:data===undefined?{}:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:data===undefined?undefined:JSON.stringify(data)});const result=await r.json();if(r.status===401){$('#app').classList.add('hidden');$('#login').classList.remove('hidden')}if(!r.ok)throw Error(result.error||'Request failed');return result}
const badge=s=>`<span class="badge ${escape(s)}">${escape(s)}</span>`;const date=s=>new Date(s).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
function tile(v,card=false){return card?`<article class="card" data-video="${v.id}">${v.media.thumbnail?`<img src="${v.media.thumbnail}" alt="${escape(v.title)}">`:'<div class="placeholder">▷</div>'}<div class="card-body">${badge(v.status)}<h3>${escape(v.title||v.id)}</h3><small>${date(v.created_at)}</small></div></article>`:`<div class="video-row" data-video="${v.id}">${v.media.thumbnail?`<img src="${v.media.thumbnail}" alt="">`:'<div class="placeholder">▷</div>'}<div><strong>${escape(v.title||v.id)}</strong><small>${date(v.created_at)}</small></div>${badge(v.status)}</div>`}
function library(){const query=$('#search').value.toLowerCase(),filter=$('#filter').value;const videos=state.episodes.filter(v=>{let m=true;if(filter==='producing')m=['queued','generating'].includes(v.status);else if(filter==='draft')m=['draft','blocked'].includes(v.status);else if(filter)m=v.status===filter;return m&&(v.title||v.id).toLowerCase().includes(query)});$('#library').innerHTML=videos.map(v=>tile(v,true)).join('')||'<div class="empty">No videos here yet. Start with a question.</div>'}
function render(){const vs=state.episodes,count=s=>vs.filter(v=>s.includes(v.status)).length;$('#ready').textContent=count(['ready']);$('#producing').textContent=count(['queued','generating']);$('#drafts').textContent=count(['draft','blocked']);$('#published').textContent=count(['published']);$('#buffer-hint').textContent=`of ${state.settings.buffer_target} buffer target`;$('#worker').textContent=state.worker.online?'● Worker online':'○ Worker offline';$('#recent').innerHTML=vs.slice(0,4).map(v=>tile(v)).join('')||'<div class="empty">Your first video starts with one good question.</div>';$('#schedule').innerHTML=`<div class="schedule-line"><span>Buffer generation</span>${badge(state.settings.generation_enabled?'enabled':'paused')}</div><div class="schedule-line"><span>Publishing</span>${badge(state.settings.publishing_enabled?'enabled':'paused')}</div><div class="schedule-line"><span>Daily slots</span><strong>${state.settings.publish_times.join(' · ')}</strong></div><p class="muted">${escape(state.settings.timezone)} · Supabase archive ${state.archive_enabled?'connected':'disabled'}</p>`;$('#jobs').innerHTML=state.jobs.map(j=>`<div class="job"><span><strong>${escape(j.kind)}</strong> ${escape(j.episode_id||'')}</span><time class="muted">${date(j.created_at)}</time>${badge(j.status)}${j.error?`<div class="job-error">${escape(j.error)}</div>`:''}</div>`).join('')||'<p class="muted">No jobs yet. This is where progress appears.</p>';library();$('#connection').textContent=`Channel: ${state.channel_id} · Playlist: ${state.playlist_id||'None'} · Public address: u.trypitch.co`}
async function refresh(){if(polling)return;polling=true;try{state=await api('/api/state');csrf=state.csrf;$('#login').classList.add('hidden');$('#app').classList.remove('hidden');render()}catch(e){if(!state)$('#login').classList.remove('hidden')}finally{polling=false}}
function tab(name){document.querySelectorAll('.tab').forEach(e=>e.classList.toggle('hidden',e.id!==name));document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));$('#breadcrumb').textContent='Workspace / '+name[0].toUpperCase()+name.slice(1);if(name==='topics')$('#topic-list').value=state.topics.join('\n');if(name==='settings'){for(const[k,v]of Object.entries(state.settings)){const e=$(`#settings-form [name="${k}"]`);if(!e)continue;if(e.type==='checkbox')e.checked=v;else e.value=Array.isArray(v)?v.join(', '):v}}}

function renderSessionEvents(){
  if(!currentSession)return;
  const q=($('#session-search')?.value||'').toLowerCase().trim();
  const events=(currentSession.events||[]).filter(e=>{
    if(e.type==='notice')return sessionFilter==='all';
    if(e.type!=='tool')return false;
    if(sessionFilter==='bash'&&e.tool!=='bash')return false;
    if(sessionFilter==='files'&&!['read','write','edit'].includes(e.tool))return false;
    if(sessionFilter==='tasks'&&e.tool!=='todowrite')return false;
    if(sessionFilter==='errors'&&e.status!=='error'&&!e.details?.error)return false;
    if(q){
      const matchable=`${e.tool||''} ${e.summary||''} ${e.details?.command||''} ${e.details?.filePath||''} ${e.details?.output||''} ${e.details?.error||''}`.toLowerCase();
      if(!matchable.includes(q))return false;
    }
    return true;
  });
  if(!events.length){
    $('#session-events-list').innerHTML='<div class="empty">No matching log entries found.</div>';
    return;
  }
  $('#session-events-list').innerHTML=events.map(e=>{
    if(e.type==='notice'){
      return `<div class="session-event" style="padding:8px 14px;color:var(--muted);font-family:monospace;font-size:11px;">${escape(e.text)}</div>`;
    }
    const isError=e.status==='error'||Boolean(e.details?.error);
    const durStr=e.duration_ms?`${(e.duration_ms/1000).toFixed(1)}s`:'';
    const timeStr=e.timestamp?new Date(e.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}):'';
    let bodyHtml='';
    if(e.tool==='bash'){
      bodyHtml=`<div class="terminal-box">${e.details.workdir?`<div class="muted" style="margin-bottom:4px">dir: ${escape(e.details.workdir)}</div>`:''}<div class="terminal-cmd"><span class="prompt">$</span> ${escape(e.details.command||'')}</div>${e.details.output?`<pre class="terminal-out">${escape(e.details.output)}</pre>`:'<div class="muted">No output recorded</div>'}</div>`;
    }else if(e.tool==='todowrite'){
      const todos=e.details.todos||[];
      bodyHtml=`<div class="todo-checklist">${todos.map(t=>`<div class="todo-item ${escape(t.status)}"><span class="todo-icon">${t.status==='completed'?'✓':t.status==='in_progress'?'►':'○'}</span><span class="todo-text">${escape(t.content)}</span><span class="todo-priority ${escape(t.priority)}">${escape(t.priority)}</span></div>`).join('')}</div>`;
    }else if(['read','write','edit'].includes(e.tool)){
      bodyHtml=`<div><strong>File:</strong> <code>${escape(e.details.filePath||'')}</code>${e.details.offset?` <small class="muted">(offset: ${e.details.offset}${e.details.limit?`, limit: ${e.details.limit}`:''})</small>`:''}${e.details.content?`<pre class="code-preview">${escape(e.details.content)}</pre>`:''}${e.details.output?`<pre class="code-preview">${escape(e.details.output)}</pre>`:''}</div>`;
    }else{
      bodyHtml=`<div>${e.details.name?`<strong>Skill:</strong> ${escape(e.details.name)}<br>`:''}${e.details.url?`<strong>URL:</strong> ${escape(e.details.url)}<br>`:''}${e.details.output?`<pre class="code-preview">${escape(e.details.output)}</pre>`:''}</div>`;
    }
    if(e.details?.error){
      bodyHtml+=`<div class="error-banner"><strong>Error:</strong> ${escape(e.details.error)}</div>`;
    }
    return `<article class="session-event tool-${escape(e.tool)} ${isError?'has-error status-error expanded':''}" data-event-id="${e.id}"><div class="session-event-header"><span class="event-status-dot"></span><span class="tool-badge ${escape(e.tool)}">${escape(e.tool)}</span><span class="event-summary">${escape(e.summary||e.tool)}</span>${durStr?`<span class="event-duration">${escape(durStr)}</span>`:''}${timeStr?`<span class="event-time">${escape(timeStr)}</span>`:''}<span class="event-chevron">▶</span></div><div class="session-event-body ${isError?'':'hidden'}">${bodyHtml}</div></article>`;
  }).join('');
}

function renderSessionLog(sessionData,rawFallback){
  currentSession=sessionData;
  isRawSession=false;
  sessionFilter='all';
  $('#session-toggle-raw').textContent='View Raw';
  $('#session-events-list').classList.remove('hidden');
  $('#session-raw-pre').classList.add('hidden');
  if(!sessionData||(!sessionData.events?.length&&!sessionData.raw&&!rawFallback)){
    $('#session-summary-bar').innerHTML='';
    $('#session-filters').innerHTML='';
    $('#session-events-list').innerHTML='<div class="empty">No session log recorded for this episode yet.</div>';
    $('#session-raw-pre').textContent='No session log recorded.';
    return;
  }
  const s=sessionData.summary||{};
  const dur=s.duration_seconds?(s.duration_seconds>=60?`${Math.floor(s.duration_seconds/60)}m ${Math.round(s.duration_seconds%60)}s`:`${s.duration_seconds}s`):'—';
  const tok=s.total_tokens?(s.total_tokens>=1000?`${(s.total_tokens/1000).toFixed(1)}k`:s.total_tokens):'—';
  const cost=s.total_cost!==undefined?`$${Number(s.total_cost).toFixed(2)}`:'—';
  const toolsDetail=Object.entries(s.tool_counts||{}).map(([k,v])=>`${k} ${v}`).join(' · ');
  $('#session-summary-bar').innerHTML=`
    <div class="session-stat"><span>Tool actions</span><strong>${s.total_tools||0}</strong><small>${escape(toolsDetail||'None')}</small></div>
    <div class="session-stat"><span>Duration</span><strong>${escape(dur)}</strong><small>Run time</small></div>
    <div class="session-stat"><span>Tokens</span><strong>${escape(tok)}</strong><small>Model context</small></div>
    <div class="session-stat"><span>Cost</span><strong>${escape(cost)}</strong><small>API spend</small></div>
    <div class="session-stat"><span>Status</span><strong>${s.errors_count?`<span style="color:#c94a40">${s.errors_count} error${s.errors_count>1?'s':''}</span>`:'<span style="color:#267957">✓ Clean</span>'}</strong><small>${s.errors_count?'Issues recorded':'All tools succeeded'}</small></div>
  `;
  const counts={
    all:(sessionData.events||[]).filter(e=>e.type==='tool').length,
    bash:s.tool_counts?.bash||0,
    files:(s.tool_counts?.read||0)+(s.tool_counts?.write||0)+(s.tool_counts?.edit||0),
    tasks:s.tool_counts?.todowrite||0,
    errors:s.errors_count||0
  };
  const filterBtns=[
    {id:'all',label:`All (${counts.all})`},
    {id:'bash',label:`Terminal (${counts.bash})`},
    {id:'files',label:`Files (${counts.files})`},
    {id:'tasks',label:`Tasks (${counts.tasks})`},
    {id:'errors',label:`Errors (${counts.errors})`}
  ];
  $('#session-filters').innerHTML=filterBtns.map(f=>`<button type="button" class="${sessionFilter===f.id?'active':''}" data-filter="${f.id}">${escape(f.label)}</button>`).join('');
  $('#session-raw-pre').textContent=sessionData.raw||rawFallback||'No session log recorded';
  if($('#session-search'))$('#session-search').value='';
  renderSessionEvents();
}

async function detail(id){
  current=id;
  const v=state.episodes.find(v=>v.id===id),data=await api(`/api/videos/${id}`);
  $('#detail-title').textContent=v.title||id;
  $('#saved-session').textContent=data.session_id ? `OpenCode session: ${data.session_id} · ${data.session_runs.length} tracked runs` : 'No saved OpenCode session. Same-session revision unavailable.';
  $('#revision-form button').disabled=!data.resume_available;
  const sb=$('#detail-status');
  if(sb){
    if(v.status==='failed'||v.error){
      sb.className='status-banner failed';
      sb.innerHTML=`<strong>Failed / Rejected</strong> · ${escape(v.error||'Video production failed or rejected by operator')}`;
    }else if(v.status==='ready'){
      sb.className='status-banner ready';
      sb.innerHTML='<strong>Ready to publish</strong> · QA checks passed; queued for release';
    }else if(v.status==='uploading'){
      sb.className='status-banner uploading';
      sb.innerHTML='<strong>Uploading</strong> · Video upload in progress or awaiting retry';
    }else if(v.status==='uploaded'){
      sb.className='status-banner ready';
      sb.innerHTML='<strong>Uploaded</strong> · Uploaded to YouTube; awaiting final publication';
    }else if(v.status==='published'){
      sb.className='status-banner published';
      sb.innerHTML='<strong>Published</strong> · Live on YouTube';
    }else if(v.status==='blocked'){
      sb.className='status-banner blocked';
      sb.innerHTML=`<strong>Blocked</strong> · ${escape(v.error||'Generation or upload blocked; inspect BLOCKED.md')}`;
    }else if(v.status==='draft'){
      sb.className='status-banner draft';
      sb.innerHTML='<strong>Draft review</strong> · Inspect video, QA and session log before approval';
    }else if(v.status==='generating'){
      sb.className='status-banner draft';
      sb.innerHTML='<strong>Generating</strong> · Richard is actively producing this episode';
    }else{
      sb.className='status-banner hidden';
    }
  }
  $('#detail-media').innerHTML=v.media.video?`<video controls preload="metadata" src="${v.media.video}"></video>`:'<p>Video will appear here when the render finishes.</p>';
  let actions='';
  if(['draft','ready'].includes(v.status)){
    actions+=`<button data-action="validate">Validate & queue</button>`;
    actions+=`<button class="publish-now-btn" data-action="publish-now">⚡ Publish now</button>`;
  }
  if(['uploading','blocked'].includes(v.status)&&!v.youtube_id){
    actions+=`<button class="publish-now-btn" data-action="publish-now">⚡ Retry upload</button>`;
  }
  if(['uploaded','blocked','uploading'].includes(v.status)&&v.youtube_id){
    actions+=`<button data-action="retry-finish">Finish existing upload</button>`;
  }
  if(v.status==='failed'){
    actions+=`<button data-action="validate">Validate & retry</button>`;
  }
  if(['draft','ready','generating'].includes(v.status)&&!v.slot){
    actions+=`<button class="danger" data-action="reject">✕ Reject video</button>`;
  }else if(['uploading','blocked'].includes(v.status)&&!v.youtube_id){
    actions+=`<button class="danger" data-action="reject">✕ Cancel / Reject</button>`;
  }
  if(v.media.video)actions+=`<a href="${v.media.video}" download>Download MP4 ↗</a>`;
  if(v.media.captions)actions+=`<a href="${v.media.captions}">Captions ↗</a>`;
  if(v.youtube_id)actions+=`<a target="_blank" rel="noopener" href="https://www.youtube.com/watch?v=${encodeURIComponent(v.youtube_id)}">YouTube ↗</a>`;
  $('#detail-actions').innerHTML=actions;
  const docs={...data.documents,session_log:data.log||'No session output yet.'};
  const tabKeys=Object.keys(docs);
  $('#doc-tabs').innerHTML=tabKeys.map(k=>`<button data-doc="${k}">${k.replace('_',' ')}</button>`).join('');
  function selectDoc(k){
    document.querySelectorAll('#doc-tabs button').forEach(b=>b.classList.toggle('active',b.dataset.doc===k));
    if(k==='session_log'){
      $('#document').classList.add('hidden');
      $('#session-log-view').classList.remove('hidden');
      renderSessionLog(data.session_log,data.log);
    }else{
      $('#session-log-view').classList.add('hidden');
      $('#document').classList.remove('hidden');
      $('#document').textContent=docs[k]||'No content';
    }
  }
  $('#doc-tabs').onclick=e=>{
    const b=e.target.closest('[data-doc]');
    if(b)selectDoc(b.dataset.doc);
  };
  const defaultDoc=docs.qa?'qa':(docs.blocked?'blocked':(docs.brief?'brief':(data.session_log?'session_log':tabKeys[0])));
  selectDoc(defaultDoc);
  $('#revision-form').classList.toggle('hidden',!['draft','failed'].includes(v.status)||!!v.slot);
  $('#reconcile-form').classList.toggle('hidden',!['uploading','uploaded','blocked'].includes(v.status));
  $('#detail-dialog').showModal();
}

$('#session-toggle-raw').onclick=()=>{
  isRawSession=!isRawSession;
  $('#session-events-list').classList.toggle('hidden',isRawSession);
  $('#session-raw-pre').classList.toggle('hidden',!isRawSession);
  $('#session-toggle-raw').textContent=isRawSession?'Formatted':'View Raw';
};
$('#session-copy-log').onclick=()=>{
  const text=currentSession?.raw||$('#session-raw-pre')?.textContent||'';
  if(!text){toast('No log content to copy');return;}
  navigator.clipboard.writeText(text).then(()=>{toast('Session log copied to clipboard')}).catch(()=>{toast('Could not copy to clipboard')});
};
$('#session-filters').onclick=e=>{
  const b=e.target.closest('[data-filter]');
  if(!b)return;
  sessionFilter=b.dataset.filter;
  document.querySelectorAll('#session-filters button').forEach(btn=>btn.classList.toggle('active',btn.dataset.filter===sessionFilter));
  renderSessionEvents();
};
$('#session-search').oninput=renderSessionEvents;
$('#session-events-list').onclick=e=>{
  const h=e.target.closest('.session-event-header');
  if(!h)return;
  const card=h.closest('.session-event');
  const body=card.querySelector('.session-event-body');
  if(!body)return;
  const willExpand=body.classList.contains('hidden');
  body.classList.toggle('hidden',!willExpand);
  card.classList.toggle('expanded',willExpand);
};

$('#login-form').onsubmit=async e=>{e.preventDefault();try{const r=await api('/api/login',{password:$('#password').value});csrf=r.csrf;$('#password').value='';await refresh()}catch(e){toast(e.message)}};
$('#logout').onclick=async()=>{await api('/api/logout',{});state=null;await refresh()};$('#new-video').onclick=()=>$('#create-dialog').showModal();
document.addEventListener('click',async e=>{
  const card=e.target.closest('[data-filter-status]');
  if(card){
    const s=card.dataset.filterStatus;
    tab('videos');
    $('#filter').value=s;
    document.querySelectorAll('#status-pills button').forEach(p=>p.classList.toggle('active',p.dataset.filter===s));
    library();
    return;
  }
  const pill=e.target.closest('#status-pills button');
  if(pill){
    const s=pill.dataset.filter;
    $('#filter').value=s;
    document.querySelectorAll('#status-pills button').forEach(p=>p.classList.toggle('active',p===pill));
    library();
    return;
  }
  const b=e.target.closest('[data-tab],[data-video],[data-close],[data-op],[data-action]');
  if(!b)return;
  try{
    if(b.dataset.tab)tab(b.dataset.tab);
    if(b.dataset.video)await detail(b.dataset.video);
    if(b.dataset.close){
      $(`#${b.dataset.close}`).close();
      if(b.dataset.close==='detail-dialog'){$('#detail-media').innerHTML='';$('#session-events-list').innerHTML='';}
    }
    if(b.dataset.op){await api(`/api/operations/${b.dataset.op}`,{});toast('Operation queued');await refresh()}
    if(b.dataset.action){
      let payload={};
      if(b.dataset.action==='reject'||b.dataset.action==='fail'){
        const reason=prompt('Reason for rejecting this video (optional):','');
        if(reason===null)return;
        payload={reason:reason.trim()||'Rejected by operator'};
      }
      await api(`/api/videos/${current}/${b.dataset.action}`,payload);
      toast(b.dataset.action==='publish-now'?'Publishing queued; video will go live shortly.':b.dataset.action==='reject'?'Video rejected.':'Operation queued; watch Activity for the result.');
      await refresh();
      if($('#detail-dialog').open)await detail(current);
    }
  }catch(e){toast(e.message)}
});
$('#create-form').onsubmit=async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;try{await api('/api/videos',Object.fromEntries(new FormData(e.target)));$('#create-dialog').close();e.target.reset();toast('Video queued. Richard will start a fresh production session.');await refresh()}catch(e){toast(e.message)}finally{b.disabled=false}};
$('#revision-form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/videos/${current}/revise`,Object.fromEntries(new FormData(e.target)));toast('Revision queued');$('#detail-dialog').close();$('#detail-media').innerHTML='';await refresh()}catch(e){toast(e.message)}};
$('#reconcile-form').onsubmit=async e=>{e.preventDefault();try{await api(`/api/videos/${current}/reconcile`,Object.fromEntries(new FormData(e.target)));toast('Reconciliation queued');await refresh()}catch(e){toast(e.message)}};
$('#settings-form').onsubmit=async e=>{e.preventDefault();const data={};for(const input of e.target.querySelectorAll('[name]'))data[input.name]=input.type==='checkbox'?input.checked:input.type==='number'?Number(input.value):input.name==='publish_times'?input.value.split(',').map(x=>x.trim()):input.value;try{await api('/api/settings',data);toast('Automation settings saved');await refresh()}catch(e){toast(e.message)}};
$('#topics-form').onsubmit=async e=>{e.preventDefault();try{await api('/api/topics',{topics:$('#topic-list').value.split('\n').map(s=>s.trim()).filter(Boolean)});toast('Topic ideas saved');await refresh()}catch(e){toast(e.message)}};
$('#search').oninput=library;
$('#filter').onchange=()=>{
  const val=$('#filter').value;
  document.querySelectorAll('#status-pills button').forEach(p=>p.classList.toggle('active',p.dataset.filter===val));
  library();
};
refresh();setInterval(refresh,5000);
