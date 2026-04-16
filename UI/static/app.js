async function toggleFavorite(productId, btn) {
  const res = await fetch(`/toggle-favorite/${productId}`, { method: "POST" });
  const data = await res.json();
  if (!data.ok) return;

  btn.classList.toggle("on", data.favorite === 1);
  btn.setAttribute("aria-pressed", data.favorite === 1 ? "true" : "false");

  const article = btn.closest(".product-card");
  const historyButton = article.querySelector(".secondary.outline");

  if (data.favorite === 1 && !historyButton) {
    location.reload();
  } else if (data.favorite === 0) {
    location.reload();
  }
}

async function showHistory(productId) {
  const box = document.getElementById(`hist-${productId}`);
  const holder = box.querySelector(".history");

  if (box.style.display === "block") {
    box.style.display = "none";
    return;
  }

  const res = await fetch(`/history/${productId}`);
  const data = await res.json();

  if (!data.ok) {
    holder.innerHTML = `<p class="history-empty">Αποτυχία φόρτωσης ιστορικού.</p>`;
    box.style.display = "block";
    return;
  }

  const rows = data.history || [];

  if (rows.length === 0) {
    holder.innerHTML = `
      <div class="history-card">
        <div class="history-title">Ιστορικό τιμών</div>
        <p class="history-empty">Δεν υπάρχει ακόμα διαθέσιμο ιστορικό.</p>
      </div>
    `;
    box.style.display = "block";
    return;
  }

  const tableRows = rows.map(r => `
    <tr>
      <td>${r.date ?? "-"}</td>
      <td>${r.price != null ? Number(r.price).toFixed(2) + "€" : "-"}</td>
      <td>${r.price_kg != null ? Number(r.price_kg).toFixed(2) + "€/kg" : "-"}</td>
    </tr>
  `).join("");

  holder.innerHTML = `
    <div class="history-card">
      <div class="history-title">Ιστορικό τιμών</div>
      <table class="history-table">
        <thead>
          <tr>
            <th>Ημερομηνία</th>
            <th>Τιμή</th>
            <th>Τιμή/kg</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
    </div>
  `;

  box.style.display = "block";
}