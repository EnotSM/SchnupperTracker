(function () {
  function toast(msg) {
    var t = document.createElement("div");
    t.className = "toast";
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2000);
  }

  function copy(text) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () {
        toast("Copied!");
      }).catch(function () {
        fallbackCopy(text);
      });
    } else {
      fallbackCopy(text);
    }
  }

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); toast("Copied!"); } catch (e) {}
    document.body.removeChild(ta);
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".copy-btn");
    if (btn) {
      copy(btn.getAttribute("data-clipboard"));
      return;
    }
    var ct = e.target.closest(".copy-text");
    if (ct) {
      copy(ct.getAttribute("data-clipboard"));
      return;
    }
    var ext = e.target.closest(".external-link-btn");
    if (ext) {
      var url = ext.getAttribute("data-url");
      if (url) window.open(url, "_blank");
      return;
    }
    var maps = e.target.closest(".maps-link");
    if (maps) {
      var mapsUrl = maps.getAttribute("data-maps-url");
      if (mapsUrl) window.open(mapsUrl, "_blank");
    }
  });

  function professionSearch() {
    var input = document.getElementById("profession-input");
    var hidden = document.getElementById("profession-id");
    var dropdown = document.getElementById("profession-dropdown");
    var tags = document.getElementById("profession-tags");
    if (!input || !dropdown || !hidden || !tags) return;

    var professions = window.PROFESSIONS || [];
    var selectedType = window.SELECTED_TYPE || 'schnupper';
    var selected = {};

    function getSelectedNames() {
      return Object.keys(selected);
    }

    function updateHidden() {
      hidden.value = getSelectedNames().join(",");
    }

    function renderTags() {
      tags.innerHTML = "";
      getSelectedNames().forEach(function (name) {
        var tag = document.createElement("span");
        tag.className =
          "inline-flex items-center gap-1 bg-teal-50 text-teal-700 text-xs px-2 py-1 rounded-full border border-teal-200";
        tag.innerHTML = name + '<button class="ml-0.5 hover:text-teal-900" data-remove="' + name.replace(/"/g, "&quot;") + '">&times;</button>';
        tags.appendChild(tag);
      });
    }

    function toggleProfession(name) {
      if (selected[name]) {
        delete selected[name];
      } else {
        selected[name] = true;
      }
      updateHidden();
      renderTags();
      renderDropdown(filterItems(input.value));
    }

    function filterItems(query) {
      var q = query.toLowerCase();
      return professions.filter(function (p) {
        if (selectedType === 'schnupper' && p.trial_count <= 0) return false;
        if (selectedType === 'lehrstelle' && p.appr_count <= 0) return false;
        if (!selectedType && p.trial_count <= 0 && p.appr_count <= 0) return false;
        return p.name.toLowerCase().indexOf(q) !== -1;
      });
    }

    function renderDropdown(results) {
      dropdown.innerHTML = "";
      if (results.length === 0) {
        dropdown.classList.add("hidden");
        return;
      }
      results.forEach(function (p) {
        var div = document.createElement("div");
        div.className =
          "px-3 py-2 text-sm cursor-pointer hover:bg-teal-50 hover:text-teal-700 transition-colors flex items-center gap-2";
        var cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "accent-teal-500 rounded";
        cb.checked = !!selected[p.name];
        cb.addEventListener("change", function (e) {
          e.stopPropagation();
          toggleProfession(p.name);
        });
        div.appendChild(cb);
        var label = document.createElement("span");
        label.textContent = p.name;
        div.appendChild(label);
        div.addEventListener("click", function (e) {
          if (e.target.tagName !== "INPUT") toggleProfession(p.name);
        });
        dropdown.appendChild(div);
      });
      dropdown.classList.remove("hidden");
    }

    function initFromUrl() {
      var val = hidden.value;
      if (val) {
        val.split(",").forEach(function (name) {
          name = name.trim();
          if (name) selected[name] = true;
        });
        renderTags();
      }
    }

    tags.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-remove]");
      if (btn) {
        var name = btn.getAttribute("data-remove");
        delete selected[name];
        updateHidden();
        renderTags();
        renderDropdown(filterItems(input.value));
      }
    });

    input.addEventListener("input", function () {
      var val = input.value;
      if (!val) {
        dropdown.classList.add("hidden");
        return;
      }
      renderDropdown(filterItems(val));
    });

    input.addEventListener("focus", function () {
      if (input.value) {
        renderDropdown(filterItems(input.value));
      } else {
        renderDropdown(filterItems(""));
      }
    });

    document.addEventListener("click", function (e) {
      if (!e.target.closest("#profession-group")) {
        dropdown.classList.add("hidden");
      }
    });

    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") dropdown.classList.add("hidden");
      if (e.key === "Enter") dropdown.classList.add("hidden");
    });

    initFromUrl();
  }

  professionSearch();

  var typeRadios = document.querySelectorAll('input[name="type"]');
  typeRadios.forEach(function (radio) {
    radio.addEventListener("change", function () {
      window.SELECTED_TYPE = this.value;
      var input = document.getElementById("profession-input");
      if (input && input.value) {
        var event = new Event("input");
        input.dispatchEvent(event);
      }
    });
  });

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".save-btn");
    if (!btn) return;
    var card = btn.closest(".listing-card");
    if (!card) return;

    var isSaved = btn.getAttribute("data-saved") === "1";

    if (isSaved) {
      fetch("/api/unsave", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listing_id: card.dataset.id }),
      })
        .then(function (r) { return r.json(); })
        .then(function () {
          toast("Removed");
          btn.setAttribute("data-saved", "0");
          btn.setAttribute("title", "Save");
          var svg = btn.querySelector("svg");
          if (svg) {
            svg.classList.remove("text-red-400", "fill-current");
            svg.classList.add("text-gray-400", "hover:text-red-400");
          }
        })
        .catch(function () { toast("Error removing"); });
    } else {
      var payload = {
        id: card.dataset.id,
        title: card.dataset.title,
        company: card.dataset.company,
        email: card.dataset.email,
        phone: card.dataset.phone,
        website: card.dataset.website,
        address: card.dataset.address,
        listing_type: card.dataset.type,
        last_updated: card.dataset.lastUpdated,
      };

      fetch("/api/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json(); })
        .then(function () {
          toast("Saved!");
          btn.setAttribute("data-saved", "1");
          btn.setAttribute("title", "Remove");
          var svg = btn.querySelector("svg");
          if (svg) {
            svg.classList.remove("text-gray-400", "hover:text-red-400");
            svg.classList.add("text-red-400", "fill-current");
          }
        })
        .catch(function () { toast("Error saving"); });
    }
  });

  var deleteBtns = document.querySelectorAll(".delete-btn");
  deleteBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var card = btn.closest("[data-id]");
      if (!card || !confirm("Remove this listing?")) return;
      var id = card.dataset.id;

      fetch("/api/save/" + id, { method: "DELETE" })
        .then(function (r) { return r.json(); })
        .then(function () {
          card.remove();
          toast("Removed");
          if (!document.querySelector("[data-id]")) {
            location.reload();
          }
        })
        .catch(function () { toast("Error removing"); });
    });
  });

  var statusSelects = document.querySelectorAll(".status-select");
  statusSelects.forEach(function (sel) {
    sel.addEventListener("change", function () {
      var card = sel.closest("[data-id]");
      if (!card) return;
      var id = card.dataset.id;
      var status = sel.value;

      fetch("/api/save/" + id + "/status", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: status }),
      })
        .then(function () {
          toast("Status updated");
          location.reload();
        })
        .catch(function () { toast("Error updating status"); });
    });
  });

  var noteInputs = document.querySelectorAll(".note-input");
  noteInputs.forEach(function (ta) {
    var timer;

    function saveNote() {
      var card = ta.closest("[data-id]");
      if (!card) return;
      var id = card.dataset.id;
      var note = ta.value;

      fetch("/api/save/" + id + "/note", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: note }),
      }).then(function (r) { return r.json(); }).then(function () {
        toast("Note saved");
      }).catch(function () {});
    }

    ta.addEventListener("blur", saveNote);
    ta.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(saveNote, 2000);
    });
  });

  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".mute-btn");
    if (!btn) return;
    var card = btn.closest("[data-id]");
    if (!card) return;
    var id = card.dataset.id;
    var muted = card.getAttribute("data-muted") === "1";

    fetch("/api/save/" + id + "/mute", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ muted: !muted }),
    })
      .then(function () { location.reload(); })
      .catch(function () { toast("Error"); });
  });

  var searchForm = document.querySelector("form[action='/']");
  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var prof = document.getElementById("profession-id").value.trim();
      var loc = document.getElementById("location").value.trim();
      var type = document.querySelector('input[name="type"]:checked');
      var url;
      if (!prof && !loc && !type) {
        url = "/";
      } else {
        var params = new URLSearchParams(new FormData(searchForm));
        url = "/?" + params.toString();
      }
      history.replaceState(null, "", url);
      fetch(url)
        .then(function (r) { return r.text(); })
        .then(function (html) {
          var parser = new DOMParser();
          var doc = parser.parseFromString(html, "text/html");
          var newRegion = doc.getElementById("results-region");
          var oldRegion = document.getElementById("results-region");
          if (newRegion && oldRegion) {
            oldRegion.outerHTML = newRegion.outerHTML;
          }
        })
        .catch(function () { toast("Search error"); });
    });
  }
})();
