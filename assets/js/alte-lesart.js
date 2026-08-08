document.addEventListener('DOMContentLoaded',()=>{
  const menu=document.querySelector('.menu-button'); const nav=document.querySelector('.nav');
  if(menu&&nav){menu.addEventListener('click',()=>{const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));});}
  const search=document.querySelector('[data-search]');
  if(search){const cards=[...document.querySelectorAll('[data-card]')]; search.addEventListener('input',()=>{const q=search.value.toLowerCase().trim(); cards.forEach(c=>{c.classList.toggle('hidden',!c.textContent.toLowerCase().includes(q));});});}
});
