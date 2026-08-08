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
});
