/* College Specs — single classic script (no modules, no fetch: file://-safe). */
(function () {
  "use strict";

  // ------------------------------------------------------------------ data
  var DATA = window.COLLEGE_DATA;
  if (!DATA) { document.body.textContent = "data.js failed to load."; return; }

  var IDX = {};
  DATA.fields.forEach(function (f, i) { IDX[f.key] = i; });
  var FIELD = {};
  DATA.fields.forEach(function (f) { FIELD[f.key] = f; });
  var SCHOOLS = DATA.schools;
  // unitid -> archived CDS URL, for schools whose admission factors are N/A because the
  // build dropped a garbled C7 parse. Absent for schools the aggregator never covered, so
  // an unexplained N/A stays unexplained rather than getting a misleading link.
  var C7_DROPPED = DATA.c7_dropped || {};

  function get(row, key) { return row[IDX[key]]; }
  function c7DroppedUrl(row) { return C7_DROPPED[String(get(row, "unitid"))] || null; }
  var byId = new Map();
  SCHOOLS.forEach(function (r) { byId.set(get(r, "unitid"), r); });

  // ------------------------------------------------------------- utilities
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function norm(s) {
    return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, " ").trim();
  }
  function debounce(fn, ms) {
    var t; return function () { clearTimeout(t); var a = arguments, self = this;
      t = setTimeout(function () { fn.apply(self, a); }, ms); };
  }
  function fmt(v, type) {
    if (v === null || v === undefined) return null;
    switch (type) {
      case "int": return Number(v).toLocaleString("en-US");
      case "usd": return "$" + Number(v).toLocaleString("en-US");
      case "frac": return (v * 100).toFixed(1) + "%";
      case "pct": return Number(v).toFixed(1) + "%";
      case "num": return Number(v).toFixed(2);
      case "ratio": return (Number.isInteger(v) ? v : Number(v).toFixed(1)) + ":1";
      default: return String(v);
    }
  }
  function webUrl(u) {
    if (!u) return null;
    return /^https?:\/\//i.test(u) ? u : "https://" + u;
  }
  function titleCase(s) {
    return String(s).toLowerCase().replace(/\b[a-z]/g, function (c) { return c.toUpperCase(); });
  }
  function copyText(text) {
    // Copy synchronously via execCommand FIRST — it completes within the click gesture,
    // before the "see prompts" link opens a new tab and steals focus (which makes the
    // async Clipboard API reject). Fall back to the Clipboard API only if execCommand fails.
    if (legacyCopy(text)) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(function () {});
    }
  }
  function legacyCopy(text) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.top = "-1000px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      ta.setSelectionRange(0, text.length);
      var ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch (e) { return false; }
  }
  var toastTimer;
  function showToast(msg) {
    var t = el.toast;
    if (!t) return;
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("show"); }, 4000);
  }
  function renderMajors(list) {
    return list.map(function (m) {
      return "<div class=\"major-row\"><span class=\"major-name\">" + esc(m[0]) +
        "</span><span class=\"major-pct\">" + Math.round(m[1] * 100) + "%</span></div>";
    }).join("");
  }

  // ------------------------------------------------------- search index
  var INDEX = SCHOOLS.map(function (r) {
    return { row: r, id: get(r, "unitid"),
             name: get(r, "name") || "",
             enroll: get(r, "enrollment") || 0,
             text: norm((get(r, "name") || "") + " " + (get(r, "city") || "") + " " + (get(r, "state") || "")) };
  });

  // Nickname/acronym aliases resolved against names at startup (largest campus wins).
  var ALIAS_DEFS = {
    "mit": "massachusetts institute of technology",
    "ucla": "university of california los angeles",
    "usc": "university of southern california",
    "cal": "university of california berkeley",
    "uc berkeley": "university of california berkeley",
    "nyu": "new york university",
    "caltech": "california institute of technology",
    "georgia tech": "georgia institute of technology",
    "virginia tech": "virginia polytechnic",
    "penn": "university of pennsylvania",
    "upenn": "university of pennsylvania",
    "penn state": "pennsylvania state university",
    "osu": "ohio state university",
    "ohio state": "ohio state university",
    "umich": "university of michigan ann arbor",
    "michigan": "university of michigan ann arbor",
    "unc": "university of north carolina at chapel hill",
    "uva": "university of virginia",
    "ut austin": "university of texas at austin",
    "tamu": "texas a m university college station",
    "texas am": "texas a m university college station",
    "jhu": "johns hopkins",
    "cmu": "carnegie mellon",
    "uiuc": "university of illinois urbana",
    "uw": "university of washington seattle",
    "uf": "university of florida",
    "fsu": "florida state university",
    "asu": "arizona state university",
    "byu": "brigham young university",
    "lsu": "louisiana state university",
    "ole miss": "university of mississippi",
    "washu": "washington university in st louis",
    "vandy": "vanderbilt",
    "uchicago": "university of chicago"
  };
  Object.keys(ALIAS_DEFS).forEach(function (alias) {
    var target = ALIAS_DEFS[alias], best = null;
    INDEX.forEach(function (e) {
      if (e.text.indexOf(target) !== -1 && (!best || e.enroll > best.enroll)) best = e;
    });
    if (best) best.text += " " + alias;
  });

  function search(query, max) {
    var q = norm(query);
    if (!q) return [];
    var tokens = q.split(" ");
    var out = [];
    INDEX.forEach(function (e) {
      var score = -1;
      if (e.text.indexOf(q) === 0) score = 100;
      else if (e.text.indexOf(" " + q) !== -1) score = 80;
      else if (e.text.indexOf(q) !== -1) score = 60;
      else if (tokens.length > 1 && tokens.every(function (t) {
        return e.text.indexOf(t) === 0 || e.text.indexOf(" " + t) !== -1;
      })) score = 50;
      if (score >= 0) out.push({ e: e, score: score });
    });
    out.sort(function (a, b) { return b.score - a.score || b.e.enroll - a.e.enroll; });
    return out.slice(0, max || 8).map(function (x) { return x.e; });
  }
  function findByName(sub) {
    var t = norm(sub), best = null;
    INDEX.forEach(function (e) {
      if (e.text.indexOf(t) !== -1 && (!best || e.enroll > best.enroll)) best = e;
    });
    return best;
  }

  // ------------------------------------------------------------- app state
  var MAX_COMPARE = 5;
  var selected = [];                       // unitids, in pick order
  var view = "compare";
  var browse = { q: "", state: "", control: "", size: "", adm: "", np: "",
                 sortKey: "enrollment", sortDir: -1, limit: 300 };
  var applyingHash = false;
  var collapsedGroups = { c7: true };      // collapsible compare groups, collapsed by default

  function writeHash() {
    var h = view === "browse" ? "#browse"
          : selected.length ? "#compare=" + selected.join(",") : "#compare";
    if (location.hash !== h) {
      applyingHash = true;
      location.hash = h;
      setTimeout(function () { applyingHash = false; }, 0);
    }
  }
  function readHash() {
    var h = location.hash || "";
    if (h.indexOf("#browse") === 0) { view = "browse"; return; }
    view = "compare";
    var m = h.match(/^#compare=([\d,]+)/);
    selected = m
      ? m[1].split(",").map(Number).filter(function (id) { return byId.has(id); })
          .slice(0, MAX_COMPARE)
      : [];
  }

  // ------------------------------------------------------------ elements
  function $(id) { return document.getElementById(id); }
  var el = {
    tabCompare: $("tab-compare"), tabBrowse: $("tab-browse"),
    viewCompare: $("view-compare"), viewBrowse: $("view-browse"),
    pickerInput: $("picker-input"), pickerList: $("picker-list"),
    chips: $("chips"), empty: $("compare-empty"), example: $("btn-example"),
    tableWrap: $("compare-table-wrap"), table: $("compare-table"), notes: $("compare-notes"),
    essayNote: $("essay-note"), toast: $("toast"),
    fSearch: $("f-search"), fState: $("f-state"), fControl: $("f-control"),
    fSize: $("f-size"), fAdm: $("f-adm"), fNp: $("f-np"), fReset: $("f-reset"),
    browseCount: $("browse-count"), goCompare: $("btn-go-compare"),
    browseTable: $("browse-table"), showMore: $("btn-show-more"),
    footerVintages: $("footer-vintages")
  };

  // ------------------------------------------------------------ compare view
  var ROWS = [
    { group: "Size & setting", items: [
      { key: "control" }, { key: "locale" }, { key: "enrollment" }] },
    { group: "Academics", items: [
      { key: "carnegie" }, { key: "stufac" }, { key: "majors" }] },
    { group: "Admissions", items: [
      { key: "adm_rate" }, { key: "app_fee" },
      { range: ["sat_v25", "sat_v75"], label: "SAT EBRW (25th–75th)" },
      { range: ["sat_m25", "sat_m75"], label: "SAT Math (25th–75th)" },
      { key: "sat_avg" },
      { range: ["act_25", "act_75"], label: "ACT composite (25th–75th)" },
      { key: "gpa" },
      { key: "test_policy" }, { key: "essay" }, { key: "yield" },
      { key: "ed_offered" }, { key: "ea_offered" }, { key: "waitlist_admitted" }] },
    { group: "Admission factors", id: "c7", collapsible: true,
      items: DATA.fields.filter(function (f) { return f.key.indexOf("c7_") === 0; })
                        .map(function (f) { return { key: f.key }; }) },
    { group: "Cost", items: [
      { key: "tuition_in" }, { key: "tuition_out" }, { key: "cost_attend" },
      { key: "net_price" }, { key: "grant_aid" },
      { key: "merit_recipients" }, { key: "merit_award_avg" },
      { key: "np_0_30" }, { key: "np_30_48" }, { key: "np_48_75" },
      { key: "np_75_110" }, { key: "np_110p" }, { key: "pct_pell" }, { key: "pct_loan" },
      { key: "debt_median" }, { key: "loan_payment" }] },
    { group: "Outcomes", items: [
      { key: "grad_rate" }, { key: "retention" }, { key: "earn_6" }, { key: "earn_10" }] },
    { group: "Diversity", items: [
      { key: "race_white" }, { key: "race_black" }, { key: "race_hisp" }, { key: "race_asian" },
      { key: "race_aian" }, { key: "race_nhpi" }, { key: "race_2mor" }, { key: "race_intl" },
      { key: "race_unkn" }] },
    { group: "Economic mobility", items: [
      { key: "oi_access" }, { key: "oi_success" }, { key: "oi_mobility" }] },
    { group: "Campus safety", items: [
      { key: "safety_violent_per1k" }, { key: "safety_property_per1k" }] }
  ];
  var BAR_TYPES = { int: 1, usd: 1, frac: 1, pct: 1, num: 1, ratio: 1 };

  function itemMeta(item) {
    if (item.range) {
      return { label: item.label, type: "range", better: "higher",
               note: null, group: FIELD[item.range[0]].group };
    }
    var f = FIELD[item.key];
    return { label: f.label, type: f.type, better: f.better, note: f.note || null, group: f.group };
  }
  function itemValue(item, row) {
    if (item.range) {
      var a = get(row, item.range[0]), b = get(row, item.range[1]);
      return (a === null || b === null) ? null : (a + b) / 2;
    }
    return get(row, item.key);
  }
  function itemDisplay(item, row) {
    if (item.range) {
      var a = get(row, item.range[0]), b = get(row, item.range[1]);
      if (a === null || b === null) return null;
      return a.toLocaleString("en-US") + "–" + b.toLocaleString("en-US");
    }
    var f = FIELD[item.key];
    return fmt(get(row, item.key), f.type);
  }

  function renderCompare() {
    var rows = selected.map(function (id) { return byId.get(id); });

    el.empty.hidden = rows.length !== 0;
    el.tableWrap.hidden = rows.length === 0;
    el.essayNote.hidden = rows.length === 0;
    el.notes.hidden = true;
    if (!rows.length) { el.table.innerHTML = ""; renderChips(); return; }

    var html = "<thead><tr><th class=\"rowlabel-col\" scope=\"col\">Spec</th>";
    rows.forEach(function (r) {
      var link = webUrl(get(r, "url"));
      var nm = esc(get(r, "name"));
      html += "<th scope=\"col\"><div class=\"sch-name\">" +
        (link ? "<a href=\"" + esc(link) + "\" target=\"_blank\" rel=\"noopener\">" + nm + "</a>" : nm) +
        "</div><div class=\"sch-sub\">" + esc(get(r, "city") || "") + ", " + esc(get(r, "state") || "") +
        " · " + esc(get(r, "control") || "") + "</div>" +
        "<button class=\"sch-remove\" data-remove=\"" + get(r, "unitid") + "\">remove</button></th>";
    });
    html += "</tr></thead><tbody>";

    var footNotes = [];
    rows.forEach(function (r) {
      if (get(r, "oi_cluster") === 1) {
        footNotes.push("<p>* " + esc(get(r, "name")) + ": mobility values are estimated for the “" +
          esc(titleCase(get(r, "oi_cluster_name") || "multi-campus")) + "” group of campuses.</p>");
      }
    });
    // Only while the Admission factors group is expanded — otherwise the note would point at
    // a † the reader cannot see (that group is collapsed by default).
    if (!collapsedGroups.c7) {
      rows.forEach(function (r) {
        var cds = c7DroppedUrl(r);
        if (cds) {
          footNotes.push("<p>† " + esc(get(r, "name")) + ": this school publishes a Common Data " +
            "Set, but its section C7 table was misread when parsed, so we show N/A instead of " +
            "wrong ratings — <a href=\"" + esc(cds) + "\" target=\"_blank\" rel=\"noopener\">" +
            "read the filing ↗</a>.</p>");
        }
      });
    }

    ROWS.forEach(function (grp) {
      var open = !grp.collapsible || !collapsedGroups[grp.id];
      html += "<tr class=\"group-row\"" + (grp.collapsible ? " data-group=\"" + grp.id + "\"" : "") + "><td>";
      html += grp.collapsible
        ? "<button type=\"button\" class=\"group-toggle\" data-group=\"" + grp.id +
          "\" aria-expanded=\"" + open + "\"><span class=\"caret\" aria-hidden=\"true\">▸</span>" +
          esc(grp.group) + "</button>"
        : esc(grp.group);
      html += "</td><td colspan=\"" + rows.length + "\">" +
              (grp.collapsible && !open
                ? "<span class=\"group-hint\">" + grp.items.length + " factors — click to expand</span>"
                : "") +
              "</td></tr>";
      if (!open) return;               // skip item rows while collapsed
      grp.items.forEach(function (item) {
        var meta = itemMeta(item);
        var vals = rows.map(function (r) { return itemValue(item, r); });
        var nonNull = vals.filter(function (v) { return v !== null && typeof v === "number"; });

        var winner = null;
        if (meta.better !== "neutral" && nonNull.length >= 2) {
          winner = meta.better === "higher" ? Math.max.apply(null, nonNull)
                                            : Math.min.apply(null, nonNull);
        }
        var barMax = null;
        if ((BAR_TYPES[meta.type] || meta.type === "range") && nonNull.length) {
          barMax = Math.max.apply(null, nonNull.map(Math.abs));
          if (!(barMax > 0)) barMax = null;
        }

        html += "<tr><td class=\"rowlabel\"" + (meta.note ? " title=\"" + esc(meta.note) + "\"" : "") + ">" +
                esc(meta.label) + "</td>";
        rows.forEach(function (r, i) {
          if (meta.type === "majors") {
            var mlist = get(r, "majors");
            html += "<td>" + (mlist && mlist.length
              ? renderMajors(mlist) : "<span class=\"cell-val cell-na\">N/A</span>") + "</td>";
            return;
          }
          if (item.key === "essay") {
            var pol = get(r, "essay");
            var sch = esc(get(r, "name"));
            html += "<td><span class=\"cell-val" + (pol === null ? " cell-na" : "") + "\">" +
              (pol === null ? "N/A" : esc(pol)) + "</span>" +
              "<span class=\"prompt-links\">prompts: " +
              "<a class=\"prompt-link\" data-school=\"" + sch + "\" href=\"https://my-supplementals.pages.dev/\" target=\"_blank\" rel=\"noopener\">My Supplementals ↗</a>" +
              " · " +
              "<a class=\"prompt-link\" data-school=\"" + sch + "\" href=\"https://www.collegevine.com/college-essay-prompts/\" target=\"_blank\" rel=\"noopener\">CollegeVine ↗</a>" +
              "</span></td>";
            return;
          }
          var v = vals[i];
          var disp = itemDisplay(item, r);
          var isBest = winner !== null && v !== null && Math.abs(v - winner) < 1e-9;
          var star = meta.group === "mob" && get(r, "oi_cluster") === 1 && disp !== null ? "*" : "";
          // A C7 N/A on a dropped school isn't "no data" — it's data we withheld because the
          // source parse was garbled. Mark it and explain once in the footnotes below.
          var dropMark = meta.group === "adm" && item.key && item.key.indexOf("c7_") === 0 &&
                         disp === null && c7DroppedUrl(r) ? "†" : "";
          html += "<td" + (isBest ? " class=\"best\"" : "") + ">";
          if (disp === null) {
            html += "<span class=\"cell-val cell-na\">N/A" + dropMark + "</span>";
          } else {
            html += "<span class=\"cell-val\">" + esc(disp) + star + "</span>";
            if (barMax !== null && typeof v === "number") {
              var w = Math.max(2, Math.abs(v) / barMax * 100);
              html += "<div class=\"bar-track\"><div class=\"bar\" style=\"width:" + w.toFixed(1) + "%\"></div></div>";
            }
          }
          html += "</td>";
        });
        html += "</tr>";
      });
    });
    html += "</tbody>";
    el.table.innerHTML = html;

    if (footNotes.length) {
      el.notes.innerHTML = footNotes.join("");
      el.notes.hidden = false;
    }
    renderChips();
  }

  function renderChips() {
    el.chips.innerHTML = selected.map(function (id) {
      var r = byId.get(id);
      return "<span class=\"chip\">" + esc(get(r, "name")) +
             "<button data-remove=\"" + id + "\" aria-label=\"Remove " + esc(get(r, "name")) + "\">×</button></span>";
    }).join("") || "<span class=\"muted\">No schools selected yet</span>";
  }

  function addSchool(id) {
    if (selected.indexOf(id) !== -1 || selected.length >= MAX_COMPARE) return;
    selected.push(id);
    writeHash(); renderCompare(); renderBrowse();
  }
  function removeSchool(id) {
    selected = selected.filter(function (x) { return x !== id; });
    writeHash(); renderCompare(); renderBrowse();
  }

  // ------------------------------------------------------------- picker
  var pickerResults = [], pickerActive = -1;

  function renderPicker() {
    if (!pickerResults.length) {
      var q = el.pickerInput.value.trim();
      if (!q) { el.pickerList.hidden = true; el.pickerInput.setAttribute("aria-expanded", "false"); return; }
      el.pickerList.innerHTML = "<li class=\"pl-none\">No matches</li>";
      el.pickerList.hidden = false; el.pickerInput.setAttribute("aria-expanded", "true");
      return;
    }
    var atCap = selected.length >= MAX_COMPARE;
    el.pickerList.innerHTML = pickerResults.map(function (e, i) {
      var added = selected.indexOf(e.id) !== -1;
      var dim = added || atCap;
      return "<li role=\"option\" data-id=\"" + e.id + "\"" +
        (i === pickerActive ? " aria-selected=\"true\"" : "") +
        (dim ? " class=\"pl-added\"" : "") + ">" +
        "<span>" + esc(e.name) + (added ? " ✓" : atCap ? " (max 5)" : "") + "</span>" +
        "<span class=\"pl-loc\">" + esc(get(e.row, "city") || "") + ", " + esc(get(e.row, "state") || "") + "</span></li>";
    }).join("");
    el.pickerList.hidden = false;
    el.pickerInput.setAttribute("aria-expanded", "true");
  }

  el.pickerInput.addEventListener("input", debounce(function () {
    pickerResults = search(el.pickerInput.value, 8);
    pickerActive = pickerResults.length ? 0 : -1;
    renderPicker();
  }, 100));
  el.pickerInput.addEventListener("keydown", function (ev) {
    if (el.pickerList.hidden) return;
    if (ev.key === "ArrowDown") { ev.preventDefault(); pickerActive = Math.min(pickerActive + 1, pickerResults.length - 1); renderPicker(); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); pickerActive = Math.max(pickerActive - 1, 0); renderPicker(); }
    else if (ev.key === "Enter") {
      ev.preventDefault();
      if (pickerActive >= 0) { addSchool(pickerResults[pickerActive].id); closePicker(); }
    }
    else if (ev.key === "Escape") { closePicker(); }
  });
  el.pickerList.addEventListener("mousedown", function (ev) {
    var li = ev.target.closest("li[data-id]");
    if (!li) return;
    ev.preventDefault();
    addSchool(Number(li.getAttribute("data-id")));
    closePicker();
  });
  el.pickerInput.addEventListener("blur", function () {
    setTimeout(function () { el.pickerList.hidden = true; }, 120);
  });
  function closePicker() {
    el.pickerInput.value = "";
    pickerResults = []; pickerActive = -1;
    el.pickerList.hidden = true;
    el.pickerInput.setAttribute("aria-expanded", "false");
    el.pickerInput.focus();
  }

  el.example.addEventListener("click", function () {
    selected = [];
    ["harvard university", "university of michigan ann arbor", "university of california berkeley"]
      .forEach(function (n) {
        var e = findByName(n);
        if (e && selected.indexOf(e.id) === -1) selected.push(e.id);
      });
    writeHash(); renderCompare(); renderBrowse();
  });

  document.addEventListener("click", function (ev) {
    var btn = ev.target.closest("[data-remove]");
    if (btn) removeSchool(Number(btn.getAttribute("data-remove")));
  });

  document.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-group]");
    if (!t) return;
    var g = t.getAttribute("data-group");
    collapsedGroups[g] = !collapsedGroups[g];
    renderCompare();
    var btn2 = el.table.querySelector("button.group-toggle[data-group=\"" + g + "\"]");
    if (btn2) btn2.focus();            // re-render destroys the old button; restore keyboard focus
  });

  // Clicking a "see prompts" link copies the school name so it can be pasted into the
  // database's search box (which we can't pre-fill via URL). We hold the navigation briefly
  // so the "copied — paste it" toast is visible BEFORE the new tab takes over the screen.
  document.addEventListener("click", function (ev) {
    var link = ev.target.closest("a.prompt-link");
    if (!link) return;
    ev.preventDefault();
    var school = link.getAttribute("data-school");
    var href = link.href;
    if (school) copyText(school);
    showToast("Copied “" + (school || "") + "” — opening the site; press Ctrl+V (⌘V on Mac) in its search box to fill it in");
    setTimeout(function () { window.open(href, "_blank", "noopener"); }, 3000);
  });

  // ------------------------------------------------------------- browse view
  var BCOLS = [
    { id: "check", label: "", noSort: true },
    { id: "name", label: "School" },
    { id: "control", label: "Type" },
    { id: "enrollment", label: "Undergrads", num: true },
    { id: "adm_rate", label: "Accept.", num: true },
    { id: "net_price", label: "Net price", num: true },
    { id: "grad_rate", label: "Grad rate", num: true },
    { id: "earn_10", label: "Earnings (10 yr)", num: true }
  ];

  function inBucket(v, spec) {
    if (!spec) return true;
    if (v === null) return false;
    var parts = spec.split("-");
    return v >= Number(parts[0]) && v < Number(parts[1]);
  }
  function browseRows() {
    var q = norm(browse.q);
    var rows = SCHOOLS.filter(function (r) {
      if (browse.state && get(r, "state") !== browse.state) return false;
      if (browse.control && get(r, "control") !== browse.control) return false;
      if (!inBucket(get(r, "enrollment"), browse.size)) return false;
      if (!inBucket(get(r, "adm_rate"), browse.adm)) return false;
      if (!inBucket(get(r, "net_price"), browse.np)) return false;
      if (q) {
        var text = norm((get(r, "name") || "") + " " + (get(r, "city") || ""));
        if (text.indexOf(q) === -1) return false;
      }
      return true;
    });
    var k = browse.sortKey, dir = browse.sortDir;
    rows.sort(function (a, b) {
      var va = get(a, k), vb = get(b, k);
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      if (typeof va === "string") return va.localeCompare(vb) * dir;
      return (va - vb) * dir;
    });
    return rows;
  }

  function renderBrowse() {
    var rows = browseRows();
    var shown = rows.slice(0, browse.limit);
    var atCap = selected.length >= MAX_COMPARE;

    var html = "<thead><tr>";
    BCOLS.forEach(function (c) {
      var arrow = browse.sortKey === c.id ? " <span class=\"arrow\">" + (browse.sortDir === 1 ? "▲" : "▼") + "</span>" : "";
      html += "<th" + (c.num ? " class=\"num" + (c.noSort ? " no-sort" : "") + "\"" : c.noSort ? " class=\"no-sort\"" : "") +
              (c.noSort ? "" : " data-sort=\"" + c.id + "\"") + ">" + c.label + arrow + "</th>";
    });
    html += "</tr></thead><tbody>";
    shown.forEach(function (r) {
      var id = get(r, "unitid");
      var isSel = selected.indexOf(id) !== -1;
      html += "<tr>" +
        "<td><input type=\"checkbox\" data-check=\"" + id + "\"" + (isSel ? " checked" : "") +
        (!isSel && atCap ? " disabled title=\"Max 5 schools\"" : "") + " aria-label=\"Select " + esc(get(r, "name")) + "\"></td>" +
        "<td class=\"b-name\">" + esc(get(r, "name")) +
        "<div class=\"b-loc\">" + esc(get(r, "city") || "") + ", " + esc(get(r, "state") || "") + "</div></td>" +
        "<td>" + esc(get(r, "control") || "") + "</td>" +
        "<td class=\"num\">" + (fmt(get(r, "enrollment"), "int") || "—") + "</td>" +
        "<td class=\"num\">" + (fmt(get(r, "adm_rate"), "frac") || "—") + "</td>" +
        "<td class=\"num\">" + (fmt(get(r, "net_price"), "usd") || "—") + "</td>" +
        "<td class=\"num\">" + (fmt(get(r, "grad_rate"), "frac") || "—") + "</td>" +
        "<td class=\"num\">" + (fmt(get(r, "earn_10"), "usd") || "—") + "</td></tr>";
    });
    html += "</tbody>";
    el.browseTable.innerHTML = html;

    el.browseCount.textContent = "Showing " + shown.length.toLocaleString("en-US") +
      " of " + rows.length.toLocaleString("en-US") + " schools" +
      (selected.length ? " · " + selected.length + " selected" : "");
    el.showMore.hidden = shown.length >= rows.length;
    el.goCompare.disabled = selected.length < 2;
    el.goCompare.textContent = "Compare selected (" + selected.length + ") →";
  }

  el.browseTable.addEventListener("change", function (ev) {
    var cb = ev.target.closest("input[data-check]");
    if (!cb) return;
    var id = Number(cb.getAttribute("data-check"));
    if (cb.checked) addSchool(id); else removeSchool(id);
  });
  el.browseTable.addEventListener("click", function (ev) {
    var th = ev.target.closest("th[data-sort]");
    if (!th) return;
    var k = th.getAttribute("data-sort");
    if (browse.sortKey === k) browse.sortDir *= -1;
    else { browse.sortKey = k; browse.sortDir = (k === "name" || k === "control") ? 1 : -1; }
    renderBrowse();
  });

  [["fSearch", "q"], ["fState", "state"], ["fControl", "control"],
   ["fSize", "size"], ["fAdm", "adm"], ["fNp", "np"]].forEach(function (pair) {
    var node = el[pair[0]], prop = pair[1];
    var handler = debounce(function () {
      browse[prop] = node.value;
      browse.limit = 300;
      renderBrowse();
    }, node.tagName === "INPUT" ? 120 : 0);
    node.addEventListener(node.tagName === "INPUT" ? "input" : "change", handler);
  });
  el.fReset.addEventListener("click", function () {
    browse.q = browse.state = browse.control = browse.size = browse.adm = browse.np = "";
    browse.limit = 300;
    el.fSearch.value = ""; el.fState.value = ""; el.fControl.value = "";
    el.fSize.value = ""; el.fAdm.value = ""; el.fNp.value = "";
    renderBrowse();
  });
  el.showMore.addEventListener("click", function () {
    browse.limit += 300;
    renderBrowse();
  });
  el.goCompare.addEventListener("click", function () {
    view = "compare"; writeHash(); syncView(); renderCompare();
  });

  // state dropdown options
  (function () {
    var states = {};
    SCHOOLS.forEach(function (r) { var s = get(r, "state"); if (s) states[s] = 1; });
    el.fState.innerHTML = "<option value=\"\">Any state</option>" +
      Object.keys(states).sort().map(function (s) { return "<option>" + s + "</option>"; }).join("");
  })();

  // ------------------------------------------------------------- view switching
  function syncView() {
    el.viewCompare.hidden = view !== "compare";
    el.viewBrowse.hidden = view !== "browse";
    el.tabCompare.setAttribute("aria-selected", String(view === "compare"));
    el.tabBrowse.setAttribute("aria-selected", String(view === "browse"));
  }
  el.tabCompare.addEventListener("click", function () { view = "compare"; writeHash(); syncView(); });
  el.tabBrowse.addEventListener("click", function () { view = "browse"; writeHash(); syncView(); renderBrowse(); });

  window.addEventListener("hashchange", function () {
    if (applyingHash) return;
    readHash(); syncView(); renderCompare(); renderBrowse();
  });

  // ------------------------------------------------------------- footer + init
  el.footerVintages.innerHTML = "<p>Data: " +
    Object.keys(DATA.vintages).map(function (k) { return esc(DATA.vintages[k]); }).join(" · ") +
    " · built " + esc(DATA.generated) + "</p>";

  readHash();
  syncView();
  renderCompare();
  renderBrowse();
})();
