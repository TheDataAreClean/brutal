    // Storage can throw (blocked cookies, sandboxed frames, some private modes) — never let it stop the script
    function storageGet(kind, key) {
      try { return window[kind].getItem(key); } catch (e) { return null; }
    }

    function storageSet(kind, key, value) {
      try { window[kind].setItem(key, value); } catch (e) {}
    }

    // Copy (content/labels.md) and the season colour table (build.py) arrive via the site-data JSON block
    var siteData = (function() {
      try { return JSON.parse(document.getElementById('site-data').textContent); } catch (e) { return {}; }
    })();

    function toggleTheme() {
      var html = document.documentElement;
      var current = html.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      storageSet('sessionStorage', 'theme', next);
    }

    var toastTimer;

    function showToast(message) {
      var toast = document.getElementById('toast');
      toast.textContent = message;
      toast.classList.add('visible');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(function() {
        toast.classList.remove('visible');
        toast.textContent = '';
      }, 2000);
    }

    // Clipboard API where available (secure contexts), else the legacy copy command; always say how it went
    function copyEmail(btn) {
      var toast = document.getElementById('toast');
      var ok = function() { showToast(toast.dataset.copied); };
      var fail = function() { showToast(toast.dataset.failed); };
      function legacyCopy() {
        var field = document.createElement('textarea');
        field.value = btn.dataset.email;
        field.setAttribute('readonly', '');
        field.style.position = 'fixed';
        field.style.opacity = '0';
        document.body.appendChild(field);
        field.select();
        var copied = false;
        try { copied = document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(field);
        (copied ? ok : fail)();
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(btn.dataset.email).then(ok, legacyCopy);
      } else {
        legacyCopy();
      }
    }

    // Seasonal accent — Bengaluru blooms
    var seasons = (siteData.seasons || []).map(function(pair) { return { light: pair[0], dark: pair[1] }; });

    var seasonNames = siteData['season-names'] || [];
    var monthNames = siteData['month-names'] || [];
    var activeSeason = new Date().getMonth();

    function applySeason(index, save) {
      if (!seasons[index]) return;
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
        swatch.style.setProperty('--swatch-light', s.light);
        swatch.style.setProperty('--swatch-dark', s.dark);
        btn.appendChild(swatch);
        btn.appendChild(document.createTextNode((monthNames[i] || '') + ' ' + siteData['pair-separator'] + ' ' + (seasonNames[i] || '')));
        btn.onclick = function(e) {
          e.stopPropagation();
          applySeason(i, true);
          setSeasonsOpen(false);
        };
        dropdown.appendChild(btn);
      });
      var info = document.createElement('div');
      info.className = 'season-info';
      info.textContent = dropdown.dataset.info || '';
      info.addEventListener('click', function(e) { e.stopPropagation(); });
      dropdown.appendChild(info);
    })();

    function setSeasonsOpen(open) {
      document.getElementById('season-dropdown').classList.toggle('open', open);
      var toggle = document.querySelector('.nav-logo-season');
      if (toggle) toggle.setAttribute('aria-expanded', String(open));
    }

    function toggleSeasons(e) {
      e.stopPropagation();
      setSeasonsOpen(!document.getElementById('season-dropdown').classList.contains('open'));
    }

    document.addEventListener('click', function() { setSeasonsOpen(false); });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') setSeasonsOpen(false);
    });

    // Local time (pauses when tab is hidden)
    (function() {
      var timer;
      function updateTime() {
        var now = new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: true });
        document.getElementById('local-time').textContent = now + ' ' + (siteData['time-suffix'] || '');
      }
      // One interval at most, and none while the tab is hidden
      function stop() { clearInterval(timer); timer = null; }
      function start() {
        stop();
        if (document.hidden) return;
        updateTime();
        timer = setInterval(updateTime, 60000);
      }
      start();
      document.addEventListener('visibilitychange', start);
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
      function(r) {
        return r.json().then(function(d) {
          var temp = d.current.temperature_2m;
          if (typeof temp !== 'number') throw new Error('no temperature');
          return Math.round(temp) + siteData['temp-unit'];
        });
      },
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
          if (typeof aqi !== 'number') throw new Error('no AQI');
          var label = aqi <= 50 ? siteData['aqi-good'] : aqi <= 100 ? siteData['aqi-moderate'] : aqi <= 150 ? siteData['aqi-sensitive'] : aqi <= 200 ? siteData['aqi-unhealthy'] : siteData['aqi-poor'];
          return aqi + ' ' + siteData['pair-separator'] + ' ' + label;
        });
      },
      function(v) { document.getElementById('aqi').textContent = v; },
      function() { document.getElementById('aqi').textContent = '--'; }
    );

    // Articles "show more": reveal the next batch, drop the button when none are left
    (function() {
      var btn = document.getElementById('articles-show-more');
      if (!btn) return;
      var batch = parseInt(btn.dataset.batch, 10) || 6;
      btn.addEventListener('click', function() {
        Array.from(document.querySelectorAll('.article-hidden')).slice(0, batch).forEach(function(el) {
          el.classList.remove('article-hidden');
        });
        if (!document.querySelector('.article-hidden')) btn.remove();
      });
    })();
