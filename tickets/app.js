const API_BASE = window.LOUD_API_BASE || "/api/v1";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = {
  q: "",
  sort: "date",
  page: 1,
  pageSize: 9,
  totalPages: 1,
};

/* ---------- API layer ---------- */

const api = {
  async listEvents({ q, sort, page, pageSize }) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (sort) params.set("sort", sort);
    params.set("page", page);
    params.set("page_size", pageSize);
    const res = await fetch(`${API_BASE}/events/?${params}`);
    if (!res.ok) throw new Error(`events list: ${res.status}`);
    return res.json();
  },
  async getEvent(id) {
    const res = await fetch(`${API_BASE}/events/${id}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`event detail: ${res.status}`);
    return res.json();
  },
  async healthz() {
    try {
      const res = await fetch(`${API_BASE}/healthz`, { cache: "no-store" });
      return res.ok;
    } catch (_) {
      return false;
    }
  },
};

/* ---------- rendering ---------- */

const fmt = {
  date(iso) {
    if (!iso) return "TBA";
    const d = new Date(iso);
    return d
      .toLocaleDateString(undefined, {
        weekday: "short",
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
      .toUpperCase();
  },
  time(iso) {
    if (!iso) return "";
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  },
  money(n) {
    if (n == null) return "—";
    return `$${Number(n).toFixed(2)}`;
  },
};

function availabilityClass(ev) {
  if (!ev.total_capacity || ev.available == null) return "";
  if (ev.available === 0) return "is-sold";
  if (ev.available / ev.total_capacity < 0.15) return "is-low";
  return "";
}

function availabilityText(ev) {
  if (ev.available == null) return "CHECK";
  if (ev.available === 0) return "SOLD OUT";
  if (ev.available / (ev.total_capacity || 1) < 0.15) return `${ev.available} LEFT`;
  return `${ev.available} SEATS`;
}

function renderGrid(events) {
  const grid = $("#event-grid");
  grid.setAttribute("aria-busy", "false");

  if (!events.length) {
    grid.innerHTML = `<li class="placeholder">no events match. try a different word.</li>`;
    return;
  }

  grid.innerHTML = events
    .map(
      (ev) => `
    <li>
      <article class="event-card" tabindex="0" role="button"
               data-id="${ev.id}" aria-label="${ev.title}, open detail">
        <div class="card-date">${fmt.date(ev.starts_at)} · ${fmt.time(ev.starts_at)}</div>
        <h3 class="card-title">${escapeHTML(ev.title)}</h3>
        <div class="card-venue">${escapeHTML(ev.venue?.name || "Venue TBA")} —
          ${escapeHTML(ev.venue?.city || "")}</div>
        <div class="card-foot">
          <span class="card-price">FROM <strong>${fmt.money(ev.min_price)}</strong></span>
          <span class="card-avail ${availabilityClass(ev)}">${availabilityText(ev)}</span>
        </div>
      </article>
    </li>
  `,
    )
    .join("");
}

function renderPaging({ count, page }) {
  state.totalPages = Math.max(1, Math.ceil(count / state.pageSize));
  $("#page-info").textContent = `PAGE ${page} / ${state.totalPages}`;
  $("#prev").disabled = page <= 1;
  $("#next").disabled = page >= state.totalPages;
}

function escapeHTML(s = "") {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
}

/* ---------- modal ---------- */

const modal = $("#event-modal");
const modalBody = $("#modal-body");

async function openEvent(id) {
  modal.showModal();
  modalBody.innerHTML = `<p class="placeholder">loading the night…</p>`;

  let ev;
  try {
    ev = await api.getEvent(id);
  } catch (err) {
    modalBody.innerHTML = `<p>API trouble — ${escapeHTML(err.message)}</p>`;
    return;
  }
  if (!ev) {
    modalBody.innerHTML = `<p>Event not found.</p>`;
    return;
  }

  modalBody.innerHTML = `
    <h2>${escapeHTML(ev.title)}</h2>
    <p class="sub">${fmt.date(ev.starts_at)} · ${fmt.time(ev.starts_at)} —
      ${escapeHTML(ev.venue?.name || "")} (${escapeHTML(ev.venue?.city || "")})</p>
    ${ev.description ? `<p class="desc">${escapeHTML(ev.description)}</p>` : ""}
    <ul class="tiers">
      ${(ev.tiers || [])
        .map(
          (t) => `
        <li class="tier">
          <span class="tier-name">${escapeHTML(t.name)}</span>
          <span class="tier-price">${fmt.money(t.price)}</span>
          <span class="tier-left ${t.available === 0 ? "is-sold" : ""}">
            ${t.available === 0 ? "SOLD OUT" : `${t.available} LEFT`}
          </span>
        </li>
      `,
        )
        .join("")}
    </ul>
  `;
}

modal.addEventListener("click", (e) => {
  if (e.target.matches("[data-close]") || e.target === modal) modal.close();
});
modal.addEventListener("cancel", (e) => {
  /* esc closes */
});

/* ---------- ticker ---------- */

function spinTicker(events) {
  if (!events?.length) return;
  const t = $("#ticker");
  const items = events.slice(0, 6).map((e) => {
    const city = e.venue?.city ? `[${e.venue.city.toUpperCase()}]` : "";
    return `${city} ${e.title.toUpperCase()} — ${fmt.date(e.starts_at)}`;
  });
  let i = 0;
  t.textContent = items[0];
  clearInterval(window.__tickerInt);
  window.__tickerInt = setInterval(() => {
    i = (i + 1) % items.length;
    t.textContent = items[i];
  }, 3200);
}

/* ---------- main load ---------- */

async function refresh() {
  $("#event-grid").setAttribute("aria-busy", "true");
  try {
    const data = await api.listEvents(state);
    renderGrid(data.results || []);
    renderPaging({ count: data.count || 0, page: data.page || state.page });
    spinTicker(data.results || []);
  } catch (err) {
    $("#event-grid").innerHTML =
      `<li class="placeholder">api is down — “${escapeHTML(err.message)}”</li>`;
    renderPaging({ count: 0, page: 1 });
  }
}

/* ---------- wiring ---------- */

document.addEventListener("click", (e) => {
  const card = e.target.closest(".event-card");
  if (card) openEvent(card.dataset.id);
});
document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" && e.key !== " ") return;
  if (e.target.classList?.contains("event-card")) {
    e.preventDefault();
    openEvent(e.target.dataset.id);
  }
});

$("#q").addEventListener(
  "input",
  debounce((e) => {
    state.q = e.target.value.trim();
    state.page = 1;
    refresh();
  }, 250),
);

$$(".sort-btn").forEach((b) =>
  b.addEventListener("click", () => {
    $$(".sort-btn").forEach((x) => x.classList.remove("is-active"));
    b.classList.add("is-active");
    state.sort = b.dataset.sort;
    state.page = 1;
    refresh();
  }),
);

$("#prev").addEventListener("click", () => {
  if (state.page > 1) {
    state.page--;
    refresh();
    window.scrollTo({ top: $("#events").offsetTop - 20, behavior: "smooth" });
  }
});
$("#next").addEventListener("click", () => {
  if (state.page < state.totalPages) {
    state.page++;
    refresh();
    window.scrollTo({ top: $("#events").offsetTop - 20, behavior: "smooth" });
  }
});

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

/* ---------- health pulse ---------- */

(async function pulse() {
  const dot = $("#health-dot");
  const ok = await api.healthz();
  dot.textContent = ok ? "● API LIVE" : "● API DOWN";
  dot.classList.toggle("ok", ok);
  dot.classList.toggle("bad", !ok);
  setTimeout(pulse, 15000);
})();

refresh();
