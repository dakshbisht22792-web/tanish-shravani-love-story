const floatingHearts = document.querySelector(".floating-hearts");
const burstZone = document.getElementById("heart-burst");
const revealNodes = document.querySelectorAll(".reveal");
const pokeGallery = document.getElementById("poke-gallery");
const finale = document.getElementById("forever");

let finaleVisible = false;

function createFloatingHeart() {
  const heart = document.createElement("span");
  heart.className = "float-heart";
  heart.textContent = "❤";
  heart.style.left = `${Math.random() * 100}%`;
  heart.style.fontSize = `${12 + Math.random() * 18}px`;
  heart.style.animationDuration = `${7 + Math.random() * 8}s`;
  heart.style.animationDelay = `${Math.random() * 1.4}s`;
  floatingHearts.appendChild(heart);

  setTimeout(() => {
    heart.remove();
  }, 16000);
}

function startFloatingHearts() {
  for (let i = 0; i < 16; i += 1) {
    setTimeout(createFloatingHeart, i * 360);
  }
  setInterval(createFloatingHeart, 650);
}

function heartBurst() {
  if (!finaleVisible) return;

  const count = 30;
  for (let i = 0; i < count; i += 1) {
    const particle = document.createElement("span");
    particle.className = "burst-heart";
    particle.textContent = Math.random() > 0.5 ? "❤" : "✨";

    const angle = (Math.PI * 2 * i) / count;
    const distance = 60 + Math.random() * 120;
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance - 24;

    particle.style.setProperty("--x", `${x}px`);
    particle.style.setProperty("--y", `${y}px`);
    particle.style.animationDuration = `${900 + Math.random() * 700}ms`;

    burstZone.appendChild(particle);
    setTimeout(() => particle.remove(), 1700);
  }
}

const revealObserver = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
      }
    }
  },
  { threshold: 0.22 }
);

for (const node of revealNodes) {
  revealObserver.observe(node);
}

function pickRandom(list, count) {
  const pool = [...list];
  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, count);
}

function renderPokemonGallery() {
  if (!pokeGallery) return;

  const options = [
    { id: 25, name: "Pikachu", line: "Sparks fly when two hearts get close." },
    { id: 133, name: "Eevee", line: "Cute beginnings, endless possibilities." },
    { id: 39, name: "Jigglypuff", line: "A soft song for a sweeter love." },
    { id: 35, name: "Clefairy", line: "Moonlight and blush, just like your story." },
    { id: 52, name: "Meowth", line: "Mischief, laughter, and love every day." },
    { id: 172, name: "Pichu", line: "Small moments, big feelings." },
    { id: 700, name: "Sylveon", line: "Ribbon-like bonds that hold forever." },
    { id: 468, name: "Togekiss", line: "Pure joy wrapped in gentle love." },
    { id: 282, name: "Gardevoir", line: "A loyal heart that always protects." },
    { id: 196, name: "Espeon", line: "Soul-deep connection and quiet trust." }
  ];

  const chosen = pickRandom(options, 6);
  pokeGallery.innerHTML = "";

  for (const item of chosen) {
    const card = document.createElement("figure");
    card.className = "poke-card reveal";
    card.innerHTML = `
      <img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${item.id}.png" alt="${item.name} artwork">
      <figcaption><strong>${item.name}</strong> ❤️ ${item.line}</figcaption>
    `;
    pokeGallery.appendChild(card);
    revealObserver.observe(card);
  }
}

const finaleObserver = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.target === finale) {
        finaleVisible = entry.isIntersecting;
        if (finaleVisible) heartBurst();
      }
    }
  },
  { threshold: 0.35 }
);

finaleObserver.observe(finale);
renderPokemonGallery();
startFloatingHearts();
setInterval(heartBurst, 2200);
