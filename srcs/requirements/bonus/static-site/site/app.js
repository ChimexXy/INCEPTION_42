const SERVICES = [
  { name: 'nginx',       kind: 'core',  desc: 'TLSv1.2/1.3 reverse proxy. The only published port of the whole stack.' },
  { name: 'wordpress',   kind: 'core',  desc: 'php-fpm 8.2 on FastCGI :9000. Installed head-less with wp-cli.' },
  { name: 'mariadb',     kind: 'core',  desc: '10.11 on a named volume. Never exposed outside the docker network.' },
  { name: 'redis',       kind: 'bonus', desc: 'Object cache for WordPress, capped at 256 MB with an LRU policy.' },
  { name: 'ftp',         kind: 'bonus', desc: 'vsftpd, chrooted on the WordPress volume, passive mode only.' },
  { name: 'adminer',     kind: 'bonus', desc: 'Single-file database UI, reachable at adminer.mozahnou.42.fr.' },
  { name: 'static-site', kind: 'bonus', desc: 'This page. nginx serving plain HTML/CSS/JS on an internal port.' },
  { name: 'status',      kind: 'bonus', desc: 'Home-made health dashboard that probes every service in the stack.' },
];

const grid = document.getElementById('stack');
for (const s of SERVICES) {
  const card = document.createElement('article');
  card.className = 'card';
  card.innerHTML =
    `<span class="tag ${s.kind}">${s.kind === 'core' ? 'mandatory' : 'bonus'}</span>` +
    `<h3>${s.name}</h3><p>${s.desc}</p>`;
  grid.appendChild(card);
}

document.getElementById('year').textContent = new Date().getFullYear();
