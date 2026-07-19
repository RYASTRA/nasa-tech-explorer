/* Client-side search over site/data/index.json using vendored MiniSearch. */
(function () {
  "use strict";
  var SEGMENT = { patent: "patent", patent_issued: "patent-issued",
                  software: "software", spinoff: "spinoff" };
  var TYPE_LABEL = { patent: "Patent", patent_issued: "Issued patent",
                     software: "Software", spinoff: "Spinoff" };
  var MAX_LIST = 300;

  var $q = document.getElementById("q");
  var $type = document.getElementById("f-type");
  var $cat = document.getElementById("f-cat");
  var $center = document.getElementById("f-center");
  var $status = document.getElementById("status");
  var $results = document.getElementById("results");

  var docs = [];
  var mini = new MiniSearch({
    fields: ["title", "abstract", "case_number"],
    storeFields: ["dataset", "slug", "case_number", "title", "category", "center", "abstract"],
    searchOptions: { prefix: true, fuzzy: 0.15, boost: { title: 3, case_number: 5 } },
  });

  function fillSelect(select, values, labeler) {
    values.forEach(function (v) {
      var opt = document.createElement("option");
      opt.value = v;
      opt.textContent = labeler ? labeler(v) : v;
      select.appendChild(opt);
    });
  }

  function countBy(key) {
    var out = {};
    docs.forEach(function (d) { if (d[key]) out[d[key]] = (out[d[key]] || 0) + 1; });
    return out;
  }

  function readState() {
    var p = new URLSearchParams(location.search);
    $q.value = p.get("q") || "";
    $type.value = p.get("type") || "";
    $cat.value = p.get("cat") || "";
    $center.value = p.get("center") || "";
  }

  function writeState() {
    var p = new URLSearchParams();
    if ($q.value) p.set("q", $q.value);
    if ($type.value) p.set("type", $type.value);
    if ($cat.value) p.set("cat", $cat.value);
    if ($center.value) p.set("center", $center.value);
    var qs = p.toString();
    history.replaceState(null, "", qs ? "?" + qs : location.pathname);
  }

  function passesFilters(d) {
    return (!$type.value || d.dataset === $type.value) &&
           (!$cat.value || d.category === $cat.value) &&
           (!$center.value || d.center === $center.value);
  }

  function card(d) {
    var li = document.createElement("li");
    var badge = document.createElement("span");
    badge.className = "badge badge-" + d.dataset;
    badge.textContent = TYPE_LABEL[d.dataset];
    var h2 = document.createElement("h2");
    var a = document.createElement("a");
    a.href = SEGMENT[d.dataset] + "/" + encodeURIComponent(d.slug) + ".html";
    a.textContent = d.title || d.case_number || d.slug;
    h2.appendChild(a);
    var meta = document.createElement("p");
    meta.className = "hit-meta";
    meta.textContent = [d.case_number, d.center, d.category].filter(Boolean).join(" · ");
    var p = document.createElement("p");
    p.textContent = d.abstract;
    li.appendChild(badge);
    li.appendChild(h2);
    li.appendChild(meta);
    li.appendChild(p);
    return li;
  }

  function render() {
    writeState();
    var hits;
    if ($q.value.trim()) {
      hits = mini.search($q.value, { filter: passesFilters });
    } else {
      hits = docs.filter(passesFilters);
    }
    $results.textContent = "";
    hits.slice(0, MAX_LIST).forEach(function (d) { $results.appendChild(card(d)); });
    $status.textContent = hits.length + " result" + (hits.length === 1 ? "" : "s") +
      (hits.length > MAX_LIST ? " (showing first " + MAX_LIST + ")" : "");
  }

  var debounceTimer;
  function debouncedRender() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(render, 120);
  }

  fetch("data/index.json")
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (payload) {
      docs = payload.rows.map(function (row, i) {
        return { id: i, dataset: row[0], slug: row[1], case_number: row[2],
                 title: row[3], category: row[4], center: row[5], abstract: row[6] };
      });
      mini.addAll(docs);
      var typeN = countBy("dataset"), catN = countBy("category"), centerN = countBy("center");
      fillSelect($type, Object.keys(TYPE_LABEL).filter(function (v) { return typeN[v]; }),
        function (v) { return TYPE_LABEL[v] + " (" + typeN[v] + ")"; });
      fillSelect($cat, Object.keys(catN).sort(),
        function (v) { return v + " (" + catN[v] + ")"; });
      fillSelect($center, Object.keys(centerN).sort(),
        function (v) { return v + " (" + centerN[v] + ")"; });
      readState();
      render();
      [$q, $type, $cat, $center].forEach(function (el) {
        el.addEventListener("input", debouncedRender);
      });
    })
    .catch(function (err) {
      $status.textContent = "Failed to load the catalog (" + err.message + "). " +
        "Try a hard refresh.";
    });
})();
