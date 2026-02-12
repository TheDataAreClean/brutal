    function toggleTheme() {
      var html = document.documentElement;
      var current = html.getAttribute('data-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
    }

    function copyEmail() {
      navigator.clipboard.writeText('hello@thedataareclean.com').then(function() {
        var toast = document.getElementById('toast');
        toast.classList.add('visible');
        setTimeout(function() { toast.classList.remove('visible'); }, 2000);
      });
    }

    // Nav background on scroll
    (function() {
      var nav = document.querySelector('nav');
      window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
          nav.classList.add('scrolled');
        } else {
          nav.classList.remove('scrolled');
        }
      });
    })();

    // Match OS setting on load
    (function() {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
      }

      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      });
    })();

    // Seasonal accent — Bengaluru blooms
    var seasons = [
      { name: 'Poinsettia',       light: '#c43568', dark: '#e88ca5' },
      { name: 'Bougainvillea',    light: '#c82852', dark: '#f0456a' },
      { name: 'Jacaranda',        light: '#7d4abf', dark: '#a878d8' },
      { name: 'Purple Bauhinia',  light: '#6d3fb0', dark: '#9b6ed0' },
      { name: 'Gulmohar',         light: '#c04520', dark: '#e8703d' },
      { name: 'Copper Pod',       light: '#9a7212', dark: '#d4a530' },
      { name: 'Rain Tree',        light: '#8e6530', dark: '#d4a870' },
      { name: 'Oleander',         light: '#b04568', dark: '#d47a92' },
      { name: 'Golden Shower',    light: '#956818', dark: '#d49a38' },
      { name: 'Indian Laburnum',  light: '#8a5f20', dark: '#c99540' },
      { name: 'Flame of Forest', light: '#b04a28', dark: '#d47a48' },
      { name: 'Pongamia',         light: '#9a6518', dark: '#d49538' }
    ];

    var monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    var activeSeason = new Date().getMonth();

    function applySeason(index) {
      activeSeason = index;
      document.documentElement.style.setProperty('--accent-light', seasons[index].light);
      document.documentElement.style.setProperty('--accent-dark', seasons[index].dark);
      var btns = document.querySelectorAll('.season-option');
      btns.forEach(function(btn, i) {
        btn.classList.toggle('active', i === index);
      });
    }

    // Default to current month
    applySeason(new Date().getMonth());

    // Build dropdown
    (function() {
      var dropdown = document.getElementById('season-dropdown');
      var currentMonth = new Date().getMonth();
      seasons.forEach(function(s, i) {
        var btn = document.createElement('button');
        btn.className = 'season-option' + (i === currentMonth ? ' active' : '');
        btn.innerHTML = '<span class="season-swatch" style="background:' + s.light + '"></span>' + monthNames[i] + ' — ' + s.name;
        btn.onclick = function(e) {
          e.stopPropagation();
          applySeason(i);
          dropdown.classList.remove('open');
        };
        dropdown.appendChild(btn);
      });
    })();

    function toggleSeasons(e) {
      e.stopPropagation();
      document.getElementById('season-dropdown').classList.toggle('open');
    }

    document.addEventListener('click', function() {
      document.getElementById('season-dropdown').classList.remove('open');
    });

    // Local time
    function updateTime() {
      var now = new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: true });
      document.getElementById('local-time').textContent = now + ' IST';
    }
    updateTime();
    setInterval(updateTime, 60000);

    // Temperature from wttr.in
    fetch('https://wttr.in/Bengaluru?format=%t')
      .then(function(r) { return r.text(); })
      .then(function(t) { document.getElementById('temperature').textContent = t.trim(); })
      .catch(function() { document.getElementById('temperature').textContent = '--'; });

    // AQI from waqi.info
    fetch('https://api.waqi.info/feed/bengaluru/?token=demo')
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.status === 'ok') {
          var aqi = d.data.aqi;
          var label = aqi <= 50 ? 'Good' : aqi <= 100 ? 'Moderate' : aqi <= 150 ? 'Unhealthy for some' : aqi <= 200 ? 'Unhealthy' : 'Poor';
          document.getElementById('aqi').textContent = aqi + ' — ' + label;
        }
      })
      .catch(function() { document.getElementById('aqi').textContent = '--'; });
