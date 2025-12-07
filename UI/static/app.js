async function toggleFavorite(id, el){
  try {
    const res = await fetch(`/toggle-favorite/${id}`, {method:'POST'});
    const data = await res.json();
    if(data.ok){
      el.classList.toggle('on', data.favorite === 1);
    } else {
      alert(data.error || 'Κάτι δεν πήγε καλά');
    }
  } catch(e){ alert('Σφάλμα δικτύου'); }
}

async function showHistory(id){
  const details = document.getElementById(`hist-${id}`);
  const box = details.querySelector('.history');
  if(details.style.display === 'none'){
    const res = await fetch(`/history/${id}`);
    const data = await res.json();
    if(data.ok){
      if(data.history.length === 0){
        box.innerHTML = "<p class='muted'>Δεν υπάρχει ιστορικό ακόμη.</p>";
      } else {
        const rows = data.history.map(h => `<tr><td>${h.date}</td><td>${(h.price ?? 0).toFixed(2)}€</td><td>${(h.price_kg ?? 0).toFixed(2)}€/kg</td></tr>`).join("");
        box.innerHTML = `<table class="history-table"><thead><tr><th>Ημερομηνία</th><th>Τιμή</th><th>Τιμή/κιλό</th></tr></thead><tbody>${rows}</tbody></table>`;
      }
    } else {
      box.innerHTML = "<p>Σφάλμα φόρτωσης ιστορικού.</p>";
    }
    details.style.display = '';
  } else {
    details.style.display = 'none';
  }
}
