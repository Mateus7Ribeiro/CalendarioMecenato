document.querySelectorAll('[data-wheel]').forEach((wheel) => {
  const button = wheel.querySelector('[data-spin]');
  const winner = wheel.querySelector('[data-winner]');
  const names = JSON.parse(wheel.dataset.names || '[]');
  button?.addEventListener('click', () => {
    if (!names.length) return;
    button.disabled = true;
    wheel.classList.remove('spinning');
    void wheel.offsetWidth;
    wheel.classList.add('spinning');
    window.setTimeout(() => {
      winner.textContent = names[Math.floor(Math.random() * names.length)];
      button.disabled = false;
    }, 2200);
  });
});
