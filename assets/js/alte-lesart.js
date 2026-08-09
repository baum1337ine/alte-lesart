document.addEventListener('DOMContentLoaded',()=>{
  const menu=document.querySelector('.menu-button');
  const nav=document.querySelector('.nav');
  if(menu&&nav){
    menu.addEventListener('click',()=>{
      const open=nav.classList.toggle('open');
      menu.setAttribute('aria-expanded',String(open));
    });
  }

  const search=document.querySelector('[data-search]');
  if(search){
    const cards=[...document.querySelectorAll('[data-card]')];
    search.addEventListener('input',()=>{
      const q=search.value.toLowerCase().trim();
      cards.forEach(c=>{c.classList.toggle('hidden',!c.textContent.toLowerCase().includes(q));});
    });
  }

  const reader=document.querySelector('.reader article');
  if(reader){
    const bar=document.createElement('div');
    bar.className='reading-progress';
    bar.setAttribute('aria-hidden','true');
    document.body.appendChild(bar);

    const button=document.createElement('button');
    button.className='focus-toggle';
    button.type='button';
    button.textContent='Fokus';
    button.setAttribute('aria-pressed','false');
    document.body.appendChild(button);

    let saved=false;
    try{ saved=localStorage.getItem('alte-lesart-focus')==='1'; }catch(_){ saved=false; }
    const setFocus=(on)=>{
      document.body.classList.toggle('focus-mode',on);
      button.setAttribute('aria-pressed',String(on));
      button.textContent=on?'Fokus aus':'Fokus';
      try{ localStorage.setItem('alte-lesart-focus',on?'1':'0'); }catch(_){}
    };
    setFocus(saved);
    button.addEventListener('click',()=>setFocus(!document.body.classList.contains('focus-mode')));

    const update=()=>{
      const rect=reader.getBoundingClientRect();
      const total=Math.max(1,reader.offsetHeight-window.innerHeight*.55);
      const read=Math.min(total,Math.max(0,-rect.top+window.innerHeight*.12));
      bar.style.width=`${Math.round((read/total)*100)}%`;
    };
    update();
    document.addEventListener('scroll',update,{passive:true});
    window.addEventListener('resize',update);
  }

  const consentKey='alte-lesart-cookie-consent';
  const analyticsId=window.ALTE_LESART_ANALYTICS_ID;
  const loadAnalytics=()=>{
    if(!analyticsId||window.__alteLesartAnalyticsLoaded) return;
    window.__alteLesartAnalyticsLoaded=true;
    window.dataLayer=window.dataLayer||[];
    window.gtag=function(){window.dataLayer.push(arguments);};
    window.gtag('js',new Date());
    window.gtag('config',analyticsId,{anonymize_ip:true});
    const s=document.createElement('script');
    s.async=true;
    s.src=`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(analyticsId)}`;
    document.head.appendChild(s);
  };
  const showConsent=()=>{
    if(!analyticsId||document.querySelector('.cookie-banner')) return;
    const banner=document.createElement('section');
    banner.className='cookie-banner';
    banner.setAttribute('aria-label','Cookie-Hinweis');
    banner.innerHTML=`<div><strong>Optionale Cookies</strong><p>Wir nutzen Google Analytics nur mit deiner Zustimmung, um öffentliche Leseseiten grob zu verbessern. Ohne Zustimmung bleibt Analytics aus.</p><a href="/alte-lesart/datenschutz.html">Datenschutz</a></div><div class="cookie-actions"><button type="button" data-consent="reject">Ablehnen</button><button type="button" data-consent="accept">Zustimmen</button></div>`;
    document.body.appendChild(banner);
    banner.addEventListener('click',(event)=>{
      const btn=event.target.closest('[data-consent]');
      if(!btn) return;
      const accepted=btn.getAttribute('data-consent')==='accept';
      try{ localStorage.setItem(consentKey,accepted?'accepted':'rejected'); }catch(_){}
      banner.remove();
      if(accepted) loadAnalytics();
    });
  };
  let consent=null;
  try{ consent=localStorage.getItem(consentKey); }catch(_){ consent=null; }
  if(consent==='accepted') loadAnalytics();
  else if(consent!=='rejected') showConsent();
  document.querySelectorAll('.consent-reset').forEach((button)=>{
    button.addEventListener('click',()=>{
      try{ localStorage.removeItem(consentKey); }catch(_){}
      showConsent();
    });
  });

});
