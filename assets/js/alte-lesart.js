document.addEventListener('DOMContentLoaded', () => {
  const input = document.querySelector('[data-filter="works"]');
  if (!input) return;
  const cards = Array.from(document.querySelectorAll('[data-work-card]'));
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    cards.forEach(card => {
      const hay = card.textContent.toLowerCase();
      card.style.display = hay.includes(q) ? '' : 'none';
    });
  });
});
