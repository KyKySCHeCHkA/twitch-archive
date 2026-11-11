const grid = document.getElementById("grid");
const search = document.getElementById("search");
const gameSelect = document.getElementById("game");
const tagSelect = document.getElementById("tag");
const sortSelect = document.getElementById("sort");

let archive = {
  vods: [],
  games: [],
  tags: []
};

function createOption(value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  return option;
}

function fillFilters() {
  archive.games.forEach(game => {
    gameSelect.append(createOption(game, game));
  });

  archive.tags.forEach(tag => {
    tagSelect.append(createOption(tag, tag));
  });
}

function filteredVods() {
  const query = search.value.trim().toLowerCase();
  const game = gameSelect.value;
  const tag = tagSelect.value;
  const sort = sortSelect.value;

  let items = archive.vods.filter(vod => {
    const matchesQuery =
      !query || vod.title.toLowerCase().includes(query);
    const matchesGame = !game || vod.game === game;
    const matchesTag = !tag || vod.tags.includes(tag);

    return matchesQuery && matchesGame && matchesTag;
  });

  if (sort === "old") {
    items.sort((a, b) => a.datetime.localeCompare(b.datetime));
  } else if (sort === "views") {
    items.sort((a, b) => b.views - a.views);
  } else {
    items.sort((a, b) => b.datetime.localeCompare(a.datetime));
  }

  return items;
}

function render() {
  const items = filteredVods();

  if (!items.length) {
    grid.innerHTML = `<p class="empty">Ничего не найдено.</p>`;
    return;
  }

  grid.innerHTML = items.map(vod => `
    <article class="vod">
      <img src="${vod.thumbnail}" alt="">
      <div class="vod-info">
        <h2>${vod.title}</h2>
        <p>${vod.date} · ${vod.game} · ${vod.views} просмотров</p>
        <div class="tags">
          ${vod.tags.map(tag => `<span>${tag}</span>`).join("")}
        </div>
        <button data-id="${vod.id}">Смотреть</button>
      </div>
    </article>
  `).join("");
}

grid.addEventListener("click", event => {
  const button = event.target.closest("button[data-id]");

  if (!button) {
    return;
  }

  const videoId = button.dataset.id;
  const parent = location.hostname;

  grid.innerHTML = `
    <div class="player">
      <iframe
        src="https://player.twitch.tv/?video=${videoId}&parent=${parent}"
        allowfullscreen>
      </iframe>
      <button id="back">← Назад к архиву</button>
    </div>
  `;

  document.getElementById("back").onclick = render;
});

[search, gameSelect, tagSelect, sortSelect].forEach(element => {
  element.addEventListener("input", render);
});

fetch("data/vods.json")
  .then(response => response.json())
  .then(data => {
    archive = data;
    fillFilters();
    render();
  })
  .catch(() => {
    grid.innerHTML = `<p class="empty">Не удалось загрузить архив.</p>`;
  });
