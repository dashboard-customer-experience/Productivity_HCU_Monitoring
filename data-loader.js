/* ============================================================================
 * data-loader.js
 * Pengganti blok __D (data 11MB yang di-embed) + window.dash.
 * Sekarang data diambil live dari folder data/ (hasil GitHub Action):
 *   daily  <- data/hcu_agg.csv
 *   lookup <- data/hcu_lookup.csv
 *   perf   <- data/hcu_perf.csv
 *   roster <- data/hcu_roster.csv
 *   ticket <- data/hcu_ticket.csv
 *
 * window.dash menyediakan API yang SAMA PERSIS seperti sebelumnya:
 *   dash.colors         -> array warna
 *   dash.data(id)       -> { status: 'ok'|'loading'|'error', data: [ {kolom: nilai}, ... ] }
 *   dash.onData(fn)     -> panggil fn setelah data siap (dan sekali lagi bila sudah siap)
 *
 * Kolom numerik otomatis dikonversi ke number supaya identik dengan data lama.
 * ========================================================================== */
(function () {
  'use strict';

  var FILES = {
    daily:  'data/hcu_agg.csv',
    lookup: 'data/hcu_lookup.csv',
    perf:   'data/hcu_perf.csv',
    roster: 'data/hcu_roster.csv',
    ticket: 'data/hcu_ticket.csv'
  };

  // Kolom yang harus jadi number (sesuai header CSV hasil agregasi).
  var NUM = {
    daily:  ['ch', 'tp', 'ag', 'sr', 'count'],
    lookup: ['id'],
    perf:   ['hour', 'count'],
    roster: [],
    ticket: ['tickets', 'fcr_sum', 'res_sum', 'res_n', 'fcr_n', 'fcr_ok20', 'fcr_ok30', 'rs_ok60', 'rs_ok120']
  };

  var store = {};   // id -> { status, data }
  var cbs = [];
  var ready = false;

  // ---- CSV parser sederhana (dukung quoted field, koma dalam quote, newline) ----
  function parseCSV(text) {
    text = text.replace(/^\uFEFF/, ''); // buang BOM
    var rows = [];
    var row = [];
    var field = '';
    var inQ = false;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (inQ) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; }
          else { inQ = false; }
        } else { field += c; }
      } else {
        if (c === '"') { inQ = true; }
        else if (c === ',') { row.push(field); field = ''; }
        else if (c === '\n') { row.push(field); field = ''; rows.push(row); row = []; }
        else if (c === '\r') { /* abaikan */ }
        else { field += c; }
      }
    }
    if (field.length || row.length) { row.push(field); rows.push(row); }
    return rows;
  }

  function toObjects(id, text) {
    var rows = parseCSV(text);
    if (!rows.length) return [];
    var cols = rows[0];
    var numSet = {};
    (NUM[id] || []).forEach(function (c) { numSet[c] = true; });
    var out = [];
    for (var r = 1; r < rows.length; r++) {
      var arr = rows[r];
      // lewati baris kosong di akhir file
      if (arr.length === 1 && arr[0] === '') continue;
      var o = {};
      for (var c = 0; c < cols.length; c++) {
        var key = cols[c];
        var val = arr[c] === undefined ? '' : arr[c];
        if (numSet[key] && val !== '') {
          var n = Number(val);
          o[key] = isNaN(n) ? val : n;
        } else {
          o[key] = val;
        }
      }
      out.push(o);
    }
    return out;
  }

  function load() {
    var keys = Object.keys(FILES);
    // tandai semua loading dulu
    keys.forEach(function (k) { store[k] = { status: 'loading', data: [] }; });

    Promise.all(keys.map(function (k) {
      // cache-buster supaya selalu ambil versi terbaru hasil Action
      var url = FILES[k] + '?t=' + Date.now();
      return fetch(url, { cache: 'no-store' })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status + ' untuk ' + FILES[k]);
          return res.text();
        })
        .then(function (text) {
          store[k] = { status: 'ok', data: toObjects(k, text) };
        })
        .catch(function (err) {
          console.error('[data-loader] gagal memuat', k, err);
          store[k] = { status: 'error', data: [] };
        });
    })).then(function () {
      ready = true;
      cbs.forEach(function (fn) { try { fn(); } catch (e) { console.error(e); } });
    });
  }

  window.dash = {
    colors: ['#c15f3c', '#3d85c6', '#6a9955', '#b8860b', '#8e6bbf', '#d94f70', '#7a7a7a'],
    data: function (id) { return store[id] || { status: 'loading', data: [] }; },
    onData: function (fn) {
      cbs.push(fn);
      if (ready) { setTimeout(fn, 0); }
    }
  };

  load();
})();
