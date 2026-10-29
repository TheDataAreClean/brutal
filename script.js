    // Storage can throw (blocked cookies, sandboxed frames, some private modes) — never let it stop the script
    function storageGet(kind, key) {
      try { return window[kind].getItem(key); } catch (e) { return null; }
    }

    function storageSet(kind, key, value) {
      try { window[kind].setItem(key, value); } catch (e) {}
    }

    // Copy comes from content/labels.md via the site-labels JSON block
    var labels = (function() {
      try { return JSON.parse(document.getElementById('site-labels').textContent); } catch (e) { return {}; }
    })();

    function toggleTheme() {
      var html = document.documentElement;
      var current = html.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      storageSet('sessionStorage', 'theme', next);
    }

    function copyEmail(btn) {
      navigator.clipboard.writeText(btn.dataset.email).then(function() {
        var toast = document.getElementById('toast');
        toast.classList.add('visible');
        setTimeout(function() { toast.classList.remove('visible'); }, 2000);
      }).catch(function() {});
    }

    // Restore theme from session, else match OS
    (function() {
      var saved = storageGet('sessionStorage', 'theme');
      if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
      } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
      }
    })();

    // Seasonal accent — Bengaluru blooms
    var seasons = [
      { light: '#c84520', dark: '#e87040' },
      { light: '#7d4abf', dark: '#a878d8' },
      { light: '#9870b0', dark: '#b898d0' },
      { light: '#b89010', dark: '#d8b030' },
      { light: '#c83020', dark: '#e86040' },
      { light: '#a89018', dark: '#c8b030' },
      { light: '#c84568', dark: '#e87898' },
      { light: '#c82852', dark: '#f0456a' },
      { light: '#8040a8', dark: '#a868c8' },
      { light: '#c85080', dark: '#e880a8' },
      { light: '#b87878', dark: '#d0a0a0' },
      { light: '#c02838', dark: '#e85060' }
    ];

    var seasonNames = labels['season-names'] || [];
    var monthNames = labels['month-names'] || [];
    var activeSeason = new Date().getMonth();

    function applySeason(index, save) {
      activeSeason = index;
      document.documentElement.style.setProperty('--accent-light', seasons[index].light);
      document.documentElement.style.setProperty('--accent-dark', seasons[index].dark);
      var btns = document.querySelectorAll('.season-option');
      btns.forEach(function(btn, i) {
        btn.classList.toggle('active', i === index);
      });
      if (save) storageSet('sessionStorage', 'season', index);
    }

    // Restore season from session, else default to current month
    var savedSeason = parseInt(storageGet('sessionStorage', 'season'), 10);
    applySeason(savedSeason >= 0 && savedSeason < seasons.length ? savedSeason : new Date().getMonth());

    // Build dropdown (safe DOM — no innerHTML)
    (function() {
      var dropdown = document.getElementById('season-dropdown');
      seasons.forEach(function(s, i) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'season-option' + (i === activeSeason ? ' active' : '');
        var swatch = document.createElement('span');
        swatch.className = 'season-swatch';
        swatch.style.background = s.light;
        btn.appendChild(swatch);
        btn.appendChild(document.createTextNode((monthNames[i] || '') + ' — ' + (seasonNames[i] || '')));
        btn.onclick = function(e) {
          e.stopPropagation();
          applySeason(i, true);
          dropdown.classList.remove('open');
        };
        dropdown.appendChild(btn);
      });
      var info = document.createElement('div');
      info.className = 'season-info';
      info.textContent = dropdown.dataset.info || '';
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
        document.getElementById('local-time').textContent = now + ' ' + (labels['time-suffix'] || '');
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
      var cached = storageGet('localStorage', key);
      var ts = storageGet('localStorage', key + '_ts');
      if (cached && ts && Date.now() - Number(ts) < 3600000) {
        onSuccess(cached);
        return;
      }
      fetch(url)
        .then(parse)
        .then(function(value) {
          storageSet('localStorage', key, value);
          storageSet('localStorage', key + '_ts', String(Date.now()));
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
          var label = aqi <= 50 ? labels['aqi-good'] : aqi <= 100 ? labels['aqi-moderate'] : aqi <= 150 ? labels['aqi-sensitive'] : aqi <= 200 ? labels['aqi-unhealthy'] : labels['aqi-poor'];
          return aqi + ' — ' + label;
        });
      },
      function(v) { document.getElementById('aqi').textContent = v; },
      function() { document.getElementById('aqi').textContent = '--'; }
    );
