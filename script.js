    function toggleTheme() {
      var html = document.documentElement;
      var current = html.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      sessionStorage.setItem('theme', next);
    }

    function copyEmail() {
      navigator.clipboard.writeText('hello@thedataareclean.com').then(function() {
        var toast = document.getElementById('toast');
        toast.classList.add('visible');
        setTimeout(function() { toast.classList.remove('visible'); }, 2000);
      });
    }

    // Restore theme from session, else match OS
    (function() {
      var saved = sessionStorage.getItem('theme');
      if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
      } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
      }
    })();

    // Seasonal accent — Bengaluru blooms
    var seasons = [
      { name: 'Flame of Forest', light: '#c84520', dark: '#e87040' },
      { name: 'Jacaranda',       light: '#7d4abf', dark: '#a878d8' },
      { name: 'Pongamia',        light: '#9870b0', dark: '#b898d0' },
      { name: 'Golden Shower',   light: '#b89010', dark: '#d8b030' },
      { name: 'Gulmohar',        light: '#c83020', dark: '#e86040' },
      { name: 'Copper Pod',      light: '#a89018', dark: '#c8b030' },
      { name: 'Oleander',        light: '#c84568', dark: '#e87898' },
      { name: 'Bougainvillea',   light: '#c82852', dark: '#f0456a' },
      { name: 'Purple Bauhinia', light: '#8040a8', dark: '#a868c8' },
      { name: 'Tabebuia Rosea',  light: '#c85080', dark: '#e880a8' },
      { name: 'Rain Tree',       light: '#b87878', dark: '#d0a0a0' },
      { name: 'Poinsettia',      light: '#c02838', dark: '#e85060' }
    ];

    var monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    var activeSeason = new Date().getMonth();

    function applySeason(index, save) {
      activeSeason = index;
      document.documentElement.style.setProperty('--accent-light', seasons[index].light);
      document.documentElement.style.setProperty('--accent-dark', seasons[index].dark);
      var btns = document.querySelectorAll('.season-option');
      btns.forEach(function(btn, i) {
        btn.classList.toggle('active', i === index);
      });
      if (save) sessionStorage.setItem('season', index);
    }

    // Restore season from session, else default to current month
    var savedSeason = sessionStorage.getItem('season');
    applySeason(savedSeason !== null ? Number(savedSeason) : new Date().getMonth());

    // Build dropdown (safe DOM — no innerHTML)
    (function() {
      var dropdown = document.getElementById('season-dropdown');
      seasons.forEach(function(s, i) {
        var btn = document.createElement('button');
        btn.className = 'season-option' + (i === activeSeason ? ' active' : '');
        var swatch = document.createElement('span');
        swatch.className = 'season-swatch';
        swatch.style.background = s.light;
        btn.appendChild(swatch);
        btn.appendChild(document.createTextNode(monthNames[i] + ' \u2014 ' + s.name));
        btn.onclick = function(e) {
          e.stopPropagation();
          applySeason(i, true);
          dropdown.classList.remove('open');
        };
        dropdown.appendChild(btn);
      });
      var info = document.createElement('div');
      info.className = 'season-info';
      info.textContent = 'colours from bengaluru\u2019s seasonal blooms';
      dropdown.appendChild(info);
    })();

    function toggleSeasons(e) {
      e.stopPropagation();
      document.getElementById('season-dropdown').classList.toggle('open');
    }

    document.addEventListener('click', function() {
      document.getElementById('season-dropdown').classList.remove('open');
    });

    // Local time (pauses when tab is hidden)
    (function() {
      var timer;
      function updateTime() {
        var now = new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: true });
        document.getElementById('local-time').textContent = now + ' IST';
      }
      function start() { updateTime(); timer = setInterval(updateTime, 60000); }
      function stop() { clearInterval(timer); }
      start();
      document.addEventListener('visibilitychange', function() {
        if (document.hidden) { stop(); } else { start(); }
      });
    })();

    // Cached fetch helper (localStorage, 1h TTL)
    function cachedFetch(key, url, parse, onSuccess, onError) {
      var cached = localStorage.getItem(key);
      var ts = localStorage.getItem(key + '_ts');
      if (cached && ts && Date.now() - Number(ts) < 3600000) {
        onSuccess(cached);
        return;
      }
      fetch(url)
        .then(parse)
        .then(function(value) {
          localStorage.setItem(key, value);
          localStorage.setItem(key + '_ts', String(Date.now()));
          onSuccess(value);
        })
        .catch(function() { onError(); });
    }

    // Temperature from Open-Meteo (cached 1h)
    cachedFetch(
      'weather_temp',
      'https://api.open-meteo.com/v1/forecast?latitude=12.97&longitude=77.59&current=temperature_2m',
      function(r) { return r.json().then(function(d) { return Math.round(d.current.temperature_2m) + '°C'; }); },
      function(v) { document.getElementById('temperature').textContent = v; },
      function() { document.getElementById('temperature').textContent = '--'; }
    );

    // AQI from Open-Meteo (cached 1h)
    cachedFetch(
      'weather_aqi',
      'https://air-quality-api.open-meteo.com/v1/air-quality?latitude=12.97&longitude=77.59&current=us_aqi',
      function(r) {
        return r.json().then(function(d) {
          var aqi = d.current.us_aqi;
          var label = aqi <= 50 ? 'Good' : aqi <= 100 ? 'Moderate' : aqi <= 150 ? 'Unhealthy for some' : aqi <= 200 ? 'Unhealthy' : 'Poor';
          return aqi + ' \u2014 ' + label;
        });
      },
      function(v) { document.getElementById('aqi').textContent = v; },
      function() { document.getElementById('aqi').textContent = '--'; }
    );
