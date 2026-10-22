/**
 * AltCode Master - Application Controller
 * Handles 0-9999 ASCII/Alt dataset, bidirectional search & converter,
 * long-press favorites, infinite chunk rendering, and PWA installation.
 */

(function () {
  'use strict';

  // --- Constants & Defaults ---
  const CHUNK_SIZE = 80;
  const LONG_PRESS_DURATION = 450;
  const STORAGE_KEY_FAVS = 'altcode_favorites_v1';
  const STORAGE_KEY_THEME = 'altcode_theme_v1';
  const STORAGE_KEY_VIEW = 'altcode_view_v1';

  // Default seed favorites if user has never added any
  const DEFAULT_FAVS = [177, 8240, 181, 8364, 176, 169, 8482, 10003, 3, 8594, 8734, 178];

  // --- State ---
  let allRecords = [];
  let currentFilteredList = [];
  let renderedCount = 0;
  let favorites = new Set();
  let selectedCode = 177; // default inspector: ±
  let currentCategory = 'all';
  let currentRange = 'all';
  let currentView = 'table'; // 'table' or 'grid'
  let isSearching = false;
  let deferredPrompt = null;

  // Long-press tracking
  let pressTimer = null;
  let pressTarget = null;
  let pressStartX = 0;
  let pressStartY = 0;
  let longPressTriggered = false;

  // DOM Elements
  const searchInput = document.getElementById('search-input');
  const searchClearBtn = document.getElementById('search-clear-btn');
  const searchModeBadge = document.getElementById('search-mode-badge');
  const inspectorGlyphBox = document.getElementById('inspector-glyph-box');
  const inspectorGlyph = document.getElementById('inspector-glyph');
  const inspectorName = document.getElementById('inspector-name');
  const inspectorCategory = document.getElementById('inspector-category');
  const inspectorCodeDec = document.getElementById('inspector-code-dec');
  const inspectorCodeHex = document.getElementById('inspector-code-hex');
  const inspectorCodeHtml = document.getElementById('inspector-code-html');
  const inspectorCodeLatex = document.getElementById('inspector-code-latex');
  const inspectorPrimaryNum = document.getElementById('inspector-primary-num');
  const inspectorSecondaryAlt = document.getElementById('inspector-secondary-alt');
  const inspectorSecPill = document.getElementById('inspector-sec-pill');
  const inspectorFavBtn = document.getElementById('inspector-fav-btn');
  const inspectorFavIcon = document.getElementById('inspector-fav-icon');
  const inspectorCard = document.getElementById('inspector-card');
  const btnToggleInspector = document.getElementById('btn-toggle-inspector');
  const inspectorToggleIcon = document.getElementById('inspector-toggle-icon');
  const btnCopyAlt = document.getElementById('btn-copy-alt');
  const btnCopySymbol = document.getElementById('btn-copy-symbol');
  const btnCopyCode = document.getElementById('btn-copy-code');
  const favoritesContainer = document.getElementById('favorites-container');
  const favCountBadge = document.getElementById('fav-count');
  const categoryTabs = document.getElementById('category-tabs');
  const rangeSelect = document.getElementById('range-select');
  const jumpInput = document.getElementById('jump-input');
  const btnJump = document.getElementById('btn-jump');
  const resultsCount = document.getElementById('results-count');
  const btnViewTable = document.getElementById('btn-view-table');
  const btnViewGrid = document.getElementById('btn-view-grid');
  const tableContainer = document.getElementById('table-container');
  const tableBody = document.getElementById('table-body');
  const gridContainer = document.getElementById('grid-container');
  const scrollAnchor = document.getElementById('scroll-anchor');
  const loadSpinner = document.getElementById('load-spinner');
  const loadStatus = document.getElementById('load-status');
  const toastContainer = document.getElementById('toast-container');
  const btnTheme = document.getElementById('btn-theme');
  const themeIcon = document.getElementById('theme-icon');
  const btnGuide = document.getElementById('btn-guide');
  const modalGuide = document.getElementById('modal-guide');
  const btnInstall = document.getElementById('btn-install');
  const modalInstall = document.getElementById('modal-install');
  const btnTriggerPwa = document.getElementById('btn-trigger-pwa');

  // Mobile Bottom Bar buttons
  const mBtnTop = document.getElementById('m-btn-top');
  const mBtnSearch = document.getElementById('m-btn-search');
  const mBtnFavs = document.getElementById('m-btn-favs');
  const mBtnGuide = document.getElementById('m-btn-guide');

  // --- Helper Record Accessors ---
  // Record structure: [code, display_glyph, name, category, alt_ansi, alt_oem, primary_alt, secondary_alt, html_ent, alias_str, is_ctrl, ctrl_badge, latex]
  const rec = {
    code: (r) => r[0],
    glyph: (r) => r[1],
    name: (r) => r[2],
    category: (r) => r[3],
    altAnsi: (r) => r[4],
    altOem: (r) => r[5],
    primaryAlt: (r) => r[6],
    secondaryAlt: (r) => r[7],
    html: (r) => r[8],
    aliases: (r) => r[9],
    isCtrl: (r) => r[10] === 1,
    ctrlBadge: (r) => r[11],
    latex: (r) => r[12] || ''
  };

  // --- Initialization ---
  function init() {
    loadDataset();
    loadFavorites();
    loadTheme();
    loadViewPreference();
    setupEventListeners();
    setupIntersectionObserver();
    registerServiceWorker();
    
    // Inspect default character (±)
    inspectCharacter(selectedCode);

    // Initial render
    applyFilterAndRender();
  }

  // Load dataset from window.ASCII_DATA
  function loadDataset() {
    if (window.ASCII_DATA && Array.isArray(window.ASCII_DATA)) {
      allRecords = window.ASCII_DATA;
    } else {
      console.warn('ASCII_DATA not preloaded, generating fallback range...');
      allRecords = [];
      for (let i = 0; i <= 9999; i++) {
        allRecords.push([i, String.fromCodePoint(i), `Character U+${i.toString(16).toUpperCase()}`, 'General', '', '', `Alt + ${i}`, '', '', '', 0, '', '']);
      }
    }
  }

  // --- Favorites Management ---
  function loadFavorites() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_FAVS);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          favorites = new Set(parsed);
        } else {
          favorites = new Set(DEFAULT_FAVS);
        }
      } else {
        favorites = new Set(DEFAULT_FAVS);
        saveFavorites();
      }
    } catch (e) {
      favorites = new Set(DEFAULT_FAVS);
    }
    renderFavoritesBar();
  }

  function saveFavorites() {
    try {
      localStorage.setItem(STORAGE_KEY_FAVS, JSON.stringify(Array.from(favorites)));
    } catch (e) {
      console.warn('Failed to save favorites to localStorage');
    }
    renderFavoritesBar();
    updateInspectorFavButton();
  }

  function toggleFavorite(code) {
    const item = allRecords[code];
    if (!item) return;

    hapticFeedback();

    if (favorites.has(code)) {
      favorites.delete(code);
      showToast(`Removed ${rec.glyph(item)} from Favorites`, 'toast-fav');
    } else {
      favorites.add(code);
      showToast(`⭐ Added ${rec.glyph(item)} (${rec.primaryAlt(item)}) to Favorites!`, 'toast-fav');
    }

    saveFavorites();

    // Trigger visual pulse on active card if in DOM
    const cardEl = document.querySelector(`[data-code="${code}"]`);
    if (cardEl) {
      cardEl.classList.add('is-favorited-pulse');
      setTimeout(() => cardEl.classList.remove('is-favorited-pulse'), 350);
      
      const starBtn = cardEl.querySelector('.table-fav-btn, .grid-card-fav');
      if (starBtn) {
        starBtn.classList.toggle('active', favorites.has(code));
      }
    }

    // If currently viewing favorites category, refresh list
    if (currentCategory === 'fav') {
      applyFilterAndRender();
    }
  }

  function renderFavoritesBar() {
    favoritesContainer.innerHTML = '';
    favCountBadge.textContent = favorites.size;

    if (favorites.size === 0) {
      favoritesContainer.innerHTML = `<span class="fav-empty-msg">No favorite signs pinned yet. Long-press any sign in the table to add it here!</span>`;
      return;
    }

    favorites.forEach((code) => {
      const item = allRecords[code];
      if (!item) return;

      const chip = document.createElement('div');
      chip.className = 'fav-chip';
      chip.setAttribute('data-fav-code', code);
      chip.title = `${rec.name(item)} (${rec.primaryAlt(item)})\nTap to copy • Hold or click × to remove`;

      const numOnly = rec.primaryAlt(item).replace('Alt + ', '');

      chip.innerHTML = `
        <span class="fav-chip-glyph">${rec.glyph(item)}</span>
        <span class="fav-chip-alt">${numOnly}</span>
        <span class="fav-chip-remove" title="Remove from favorites" data-remove="${code}">×</span>
      `;

      // Tap favorite: inspect and copy symbol
      chip.addEventListener('click', (e) => {
        if (e.target.dataset.remove) {
          e.stopPropagation();
          toggleFavorite(code);
          return;
        }
        inspectCharacter(code);
        copyToClipboard(rec.glyph(item), `Copied '${rec.glyph(item)}' to clipboard!`);
      });

      // Long press favorite: remove
      setupLongPress(chip, () => toggleFavorite(code));

      favoritesContainer.appendChild(chip);
    });
  }

  // --- Inspector Card ---
  function inspectCharacter(code) {
    selectedCode = code;
    const item = allRecords[code];
    if (!item) return;

    const glyphStr = rec.glyph(item);
    const primaryAltStr = rec.primaryAlt(item);
    const secAltStr = rec.secondaryAlt(item);
    const hexStr = 'U+' + code.toString(16).toUpperCase().padStart(4, '0');
    const htmlEntity = rec.html(item) ? `&${rec.html(item)};` : `&#${code};`;

    inspectorGlyph.textContent = glyphStr;
    inspectorName.textContent = rec.name(item);
    inspectorCategory.textContent = rec.category(item);
    inspectorCodeDec.textContent = `Code: ${code}`;
    inspectorCodeHex.textContent = hexStr;
    inspectorCodeHtml.textContent = htmlEntity;

    const latexCmd = rec.latex(item);
    if (inspectorCodeLatex) {
      if (latexCmd) {
        inspectorCodeLatex.textContent = latexCmd;
        inspectorCodeLatex.style.display = 'inline-block';
      } else {
        inspectorCodeLatex.textContent = '';
        inspectorCodeLatex.style.display = 'none';
      }
    }

    // Alt key badge
    const primaryDigits = primaryAltStr.replace('Alt + ', '');
    inspectorPrimaryNum.textContent = primaryDigits;

    // Secondary Alt key pills
    if (secAltStr) {
      inspectorSecondaryAlt.style.display = 'flex';
      inspectorSecPill.textContent = secAltStr;
    } else {
      inspectorSecondaryAlt.style.display = 'none';
    }

    updateInspectorFavButton();

    // Highlight row/card in table/grid if rendered
    document.querySelectorAll('.ascii-table tr.is-selected, .grid-card.is-selected').forEach((el) => {
      el.classList.remove('is-selected');
    });
    const targetEl = document.querySelector(`[data-code="${code}"]`);
    if (targetEl) {
      targetEl.classList.add('is-selected');
    }
  }

  function updateInspectorFavButton() {
    const isFav = favorites.has(selectedCode);
    inspectorFavBtn.classList.toggle('active', isFav);
    inspectorFavIcon.textContent = isFav ? '⭐' : '☆';
    inspectorFavBtn.title = isFav ? 'Remove from Favorites' : 'Add to Favorites';
  }

  // --- Long-Press Event Listener Engine ---
  function setupLongPress(element, callback) {
    let timer = null;
    let didTrigger = false;
    let startX = 0;
    let startY = 0;

    function start(e) {
      didTrigger = false;
      const point = e.touches ? e.touches[0] : e;
      startX = point.clientX;
      startY = point.clientY;
      element.classList.add('is-pressing');

      timer = setTimeout(() => {
        didTrigger = true;
        element.classList.remove('is-pressing');
        callback();
      }, LONG_PRESS_DURATION);
    }

    function move(e) {
      if (!timer) return;
      const point = e.touches ? e.touches[0] : e;
      const dx = Math.abs(point.clientX - startX);
      const dy = Math.abs(point.clientY - startY);
      // Cancel if finger moved more than 10px (user is scrolling)
      if (dx > 10 || dy > 10) {
        cancel();
      }
    }

    function cancel() {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      element.classList.remove('is-pressing');
    }

    function end(e) {
      cancel();
      if (didTrigger && e.cancelable) {
        e.preventDefault();
      }
    }

    // Touch events for mobile phones
    element.addEventListener('touchstart', start, { passive: true });
    element.addEventListener('touchmove', move, { passive: true });
    element.addEventListener('touchend', end);
    element.addEventListener('touchcancel', cancel);

    // Mouse events for desktop browsers
    element.addEventListener('mousedown', (e) => {
      if (e.button === 0) start(e);
    });
    element.addEventListener('mousemove', move);
    element.addEventListener('mouseup', end);
    element.addEventListener('mouseleave', cancel);
  }

  // --- Bidirectional Search & Converter ---
  function handleSearch(query) {
    const q = query.trim();

    if (!q) {
      isSearching = false;
      searchClearBtn.style.display = 'none';
      searchModeBadge.style.display = 'none';
      applyFilterAndRender();
      return;
    }

    isSearching = true;
    searchClearBtn.style.display = 'block';

    const isDigits = /^\d+$/.test(q);
    const isSingleSymbol = q.length === 1 && !/^[a-zA-Z0-9]$/.test(q);

    if (isDigits) {
      searchModeBadge.style.display = 'block';
      searchModeBadge.textContent = 'Digits Mode';
      searchModeBadge.className = 'search-badge badge-digits';
    } else if (isSingleSymbol) {
      searchModeBadge.style.display = 'block';
      searchModeBadge.textContent = 'Symbol Mode';
      searchModeBadge.className = 'search-badge badge-symbol';
    } else {
      searchModeBadge.style.display = 'block';
      searchModeBadge.textContent = 'Search';
      searchModeBadge.className = 'search-badge badge-text';
    }

    const qLower = q.toLowerCase();
    const scoredResults = [];
    const numVal = isDigits ? parseInt(q, 10) : null;

    for (let i = 0; i < allRecords.length; i++) {
      const item = allRecords[i];
      const code = rec.code(item);
      const glyph = rec.glyph(item);
      const name = rec.name(item).toLowerCase();
      const altAnsi = rec.altAnsi(item);
      const altOem = rec.altOem(item);
      const aliases = rec.aliases(item).toLowerCase();
      const html = rec.html(item).toLowerCase();

      let score = 0;

      // 1. Exact Glyph Match (user entered symbol: ±, ‰, µ, etc.)
      if (q === glyph) {
        score += 2000;
      }

      // 2. Numeric / Alt Code Match (user entered digits: 177, 0137, 241, 8240, etc.)
      if (isDigits) {
        if (numVal === code) score += 1000;
        if (altAnsi === q || (altAnsi.endsWith(q) && q.length >= 2)) score += 900;
        if (altOem === q) score += 850;
        if (code.toString().startsWith(q)) score += 400;
        if (code.toString().includes(q)) score += 100;
      } else {
        // 3. Text Name & Alias Match (e.g. "plus minus", "mu", "permille", "euro", etc.)
        const nameWords = name.match(/[a-z0-9+-]+/g) || [];
        const aliasWords = aliases.match(/[a-z0-9+-]+/g) || [];
        const latex = rec.latex(item);

        if (latex) {
          const lLower = latex.toLowerCase();
          const lClean = lLower.replace(/[\{\}\\]/g, '');
          const qClean = qLower.replace(/[\{\}\\]/g, '');
          if (qLower === lLower || (qClean && qClean === lClean)) {
            score += 1500;
          } else if (lLower.includes(qLower) || (qClean.length >= 2 && lClean.includes(qClean))) {
            score += 750;
          }
        }

        if (name === qLower) {
          score += 1200;
        } else if (aliasWords.includes(qLower)) {
          score += 1000;
        } else if (nameWords.includes(qLower)) {
          score += 900;
        } else if (aliases.includes(qLower)) {
          score += 750; // exact phrase in alias
        } else if (name.includes(qLower)) {
          score += 700; // exact phrase in name
        } else if (aliasWords.some((w) => w.startsWith(qLower))) {
          score += 550;
        } else if (nameWords.some((w) => w.startsWith(qLower))) {
          score += 450;
        } else if (html && (html === qLower || html.includes(qLower))) {
          score += 600;
        } else if (qLower.length > 3 && (name.includes(qLower) || aliases.includes(qLower))) {
          score += 200;
        } else if (rec.category(item).toLowerCase() === qLower) {
          score += 150;
        }
      }

      if (score > 0) {
        scoredResults.push({ score, item });
      }
    }

    // Sort by relevance score descending, then by code ascending
    scoredResults.sort((a, b) => b.score - a.score || a.item[0] - b.item[0]);
    currentFilteredList = scoredResults.map((r) => r.item);

    // Auto-inspect top result immediately
    if (currentFilteredList.length > 0) {
      inspectCharacter(rec.code(currentFilteredList[0]));
    }

    renderFilteredResults();
  }

  // --- Filtering & Chunk Rendering ---
  function applyFilterAndRender() {
    if (isSearching) {
      return;
    }

    let filtered = allRecords;

    // 1. Filter by category
    if (currentCategory === 'fav') {
      filtered = filtered.filter((item) => favorites.has(rec.code(item)));
    } else if (currentCategory === 'all') {
      // Keep all
    } else if (currentCategory === 'ASCII') {
      filtered = filtered.filter((item) => rec.code(item) < 128);
    } else if (currentCategory === 'Latin-1') {
      filtered = filtered.filter((item) => rec.code(item) >= 128 && rec.code(item) <= 255);
    } else {
      filtered = filtered.filter((item) => rec.category(item) === currentCategory);
    }

    // 2. Filter by range
    if (currentRange !== 'all') {
      const parts = currentRange.split('-');
      const start = parseInt(parts[0], 10);
      const end = parseInt(parts[1], 10);
      filtered = filtered.filter((item) => {
        const c = rec.code(item);
        return c >= start && c <= end;
      });
    }

    currentFilteredList = filtered;
    renderFilteredResults();
  }

  function renderFilteredResults() {
    renderedCount = 0;
    tableBody.innerHTML = '';
    gridContainer.innerHTML = '';

    const count = currentFilteredList.length;
    resultsCount.textContent = `Showing ${count.toLocaleString()} ${count === 1 ? 'code' : 'codes'}`;

    if (count === 0) {
      const emptyHtml = `
        <div style="text-align: center; padding: 40px 16px; color: var(--text-tertiary);">
          <div style="font-size: 2.2rem; margin-bottom: 8px;">🔍</div>
          <div style="font-size: 1rem; font-weight: 600; color: var(--text-secondary);">No matching codes found</div>
          <div style="font-size: 0.8rem; margin-top: 4px;">Try searching for digits (e.g. 177, 0137) or symbol name (e.g. "plus minus", "mu").</div>
        </div>
      `;
      if (currentView === 'table') {
        tableBody.innerHTML = `<tr><td colspan="7">${emptyHtml}</td></tr>`;
      } else {
        gridContainer.innerHTML = emptyHtml;
      }
      loadStatus.textContent = '';
      return;
    }

    renderNextChunk();
  }

  function renderNextChunk() {
    if (renderedCount >= currentFilteredList.length) {
      loadSpinner.style.display = 'none';
      loadStatus.textContent = `End of results (${currentFilteredList.length.toLocaleString()} items)`;
      return;
    }

    loadSpinner.style.display = 'inline-block';
    loadStatus.textContent = 'Loading more codes...';

    const end = Math.min(renderedCount + CHUNK_SIZE, currentFilteredList.length);
    const fragment = document.createDocumentFragment();

    for (let i = renderedCount; i < end; i++) {
      const item = currentFilteredList[i];
      const code = rec.code(item);

      if (currentView === 'table') {
        const tr = createTableRow(item);
        fragment.appendChild(tr);
      } else {
        const card = createGridCard(item);
        fragment.appendChild(card);
      }
    }

    if (currentView === 'table') {
      tableBody.appendChild(fragment);
    } else {
      gridContainer.appendChild(fragment);
    }

    renderedCount = end;

    if (renderedCount >= currentFilteredList.length) {
      loadSpinner.style.display = 'none';
      loadStatus.textContent = `All ${currentFilteredList.length.toLocaleString()} codes loaded`;
    } else {
      loadSpinner.style.display = 'none';
      loadStatus.textContent = `Scroll down for more (${renderedCount.toLocaleString()} / ${currentFilteredList.length.toLocaleString()})`;
    }
  }

  // --- Table Row Factory ---
  function createTableRow(item) {
    const code = rec.code(item);
    const isFav = favorites.has(code);
    const isSelected = selectedCode === code;
    const tr = document.createElement('tr');
    tr.setAttribute('data-code', code);
    if (isSelected) tr.classList.add('is-selected');

    const primaryAlt = rec.primaryAlt(item);
    const secAlt = rec.secondaryAlt(item);
    const glyphStr = rec.glyph(item);
    const isCtrl = rec.isCtrl(item);
    const ctrlBadge = rec.ctrlBadge(item);

    tr.innerHTML = `
      <td class="col-fav">
        <button class="table-fav-btn ${isFav ? 'active' : ''}" data-fav-btn="${code}" title="${isFav ? 'Remove Favorite' : 'Add to Favorites'}">
          ${isFav ? '⭐' : '☆'}
        </button>
      </td>
      <td class="col-code">${code}</td>
      <td class="col-glyph" data-copy-glyph="${code}" title="Tap to copy symbol">
        ${isCtrl && ctrlBadge ? `<span class="table-ctrl-badge">${ctrlBadge}</span>` : `<span class="table-glyph">${glyphStr}</span>`}
      </td>
      <td class="col-alt" data-copy-alt="${code}" title="Tap to copy Alt code">
        <span class="alt-combo-badge">${primaryAlt}</span>
        ${secAlt ? `<span class="alt-combo-secondary">${secAlt}</span>` : ''}
      </td>
      <td class="col-name">
        <span class="table-name">${rec.name(item)}</span>
        ${rec.aliases(item) ? `<span class="table-aliases">${rec.aliases(item).slice(0, 45)}...</span>` : ''}
      </td>
      <td class="col-cat">
        <span class="tag tag-cat">${rec.category(item)}</span>
      </td>
      <td class="col-copy">
        <button class="btn-table-copy" data-copy="${code}">Copy</button>
      </td>
    `;

    // Row click: inspect and highlight (and copy on mobile)
    tr.addEventListener('click', (e) => {
      if (e.target.closest('[data-fav-btn]')) {
        e.stopPropagation();
        toggleFavorite(code);
        return;
      }
      if (e.target.closest('[data-copy]') || e.target.closest('[data-copy-glyph]')) {
        e.stopPropagation();
        inspectCharacter(code);
        copyToClipboard(glyphStr, `Copied '${glyphStr}' to clipboard!`);
        return;
      }
      if (e.target.closest('[data-copy-alt]')) {
        e.stopPropagation();
        inspectCharacter(code);
        copyToClipboard(primaryAlt, `Copied '${primaryAlt}' to clipboard!`);
        return;
      }
      inspectCharacter(code);
      if (window.innerWidth <= 768) {
        copyToClipboard(glyphStr, `Copied '${glyphStr}' (${primaryAlt})`);
      }
    });

    // Long press to favorite on whole row or glyph box
    setupLongPress(tr, () => toggleFavorite(code));

    return tr;
  }

  // --- Grid Card Factory ---
  function createGridCard(item) {
    const code = rec.code(item);
    const isFav = favorites.has(code);
    const isSelected = selectedCode === code;
    const card = document.createElement('div');
    card.className = `grid-card ${isSelected ? 'is-selected' : ''}`;
    card.setAttribute('data-code', code);

    const primaryAlt = rec.primaryAlt(item).replace('Alt + ', '');
    const glyphStr = rec.glyph(item);
    const isCtrl = rec.isCtrl(item);
    const ctrlBadge = rec.ctrlBadge(item);

    card.innerHTML = `
      <button class="grid-card-fav ${isFav ? 'active' : ''}" data-fav-btn="${code}" title="Toggle Favorite">
        ${isFav ? '⭐' : '☆'}
      </button>
      <span class="grid-card-code">#${code}</span>
      <div class="grid-glyph">
        ${isCtrl && ctrlBadge ? `<span class="table-ctrl-badge">${ctrlBadge}</span>` : glyphStr}
      </div>
      <span class="grid-card-alt">Alt ${primaryAlt}</span>
      <span class="grid-card-name">${rec.name(item)}</span>
      <div class="hold-ring"></div>
    `;

    card.addEventListener('click', (e) => {
      if (e.target.closest('[data-fav-btn]')) {
        e.stopPropagation();
        toggleFavorite(code);
        return;
      }
      inspectCharacter(code);
      copyToClipboard(glyphStr, `Copied '${glyphStr}' to clipboard!`);
    });

    // Long-press to toggle favorite
    setupLongPress(card, () => toggleFavorite(code));

    return card;
  }

  // --- Infinite Scroll (Intersection Observer) ---
  function setupIntersectionObserver() {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting && renderedCount < currentFilteredList.length) {
              renderNextChunk();
            }
          });
        },
        { rootMargin: '400px' }
      );
      observer.observe(scrollAnchor);
    } else {
      // Fallback for older browsers
      window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
          if (renderedCount < currentFilteredList.length) {
            renderNextChunk();
          }
        }
      });
    }
  }

  // --- Event Listeners Setup ---
  function setupEventListeners() {
    // 1. Search Input
    let debounceTimer = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        handleSearch(e.target.value);
      }, 60);
    });

    searchClearBtn.addEventListener('click', () => {
      searchInput.value = '';
      searchInput.focus();
      handleSearch('');
    });

    // Quick example buttons
    document.querySelectorAll('.pill-example').forEach((btn) => {
      btn.addEventListener('click', () => {
        const query = btn.dataset.query;
        searchInput.value = query;
        searchInput.focus();
        handleSearch(query);
      });
    });

    // 2. Inspector Copy Buttons
    btnCopyAlt.addEventListener('click', () => {
      const item = allRecords[selectedCode];
      if (item) {
        copyToClipboard(rec.primaryAlt(item), `Copied '${rec.primaryAlt(item)}' to clipboard!`);
      }
    });

    btnCopySymbol.addEventListener('click', () => {
      const item = allRecords[selectedCode];
      if (item) {
        copyToClipboard(rec.glyph(item), `Copied symbol '${rec.glyph(item)}' to clipboard!`);
      }
    });

    btnCopyCode.addEventListener('click', () => {
      copyToClipboard(selectedCode.toString(), `Copied code '${selectedCode}' to clipboard!`);
    });

    if (inspectorCodeDec) {
      inspectorCodeDec.addEventListener('click', () => {
        copyToClipboard(selectedCode.toString(), `Copied decimal code '${selectedCode}' to clipboard!`);
      });
    }

    if (inspectorCodeHex) {
      inspectorCodeHex.addEventListener('click', () => {
        const hexStr = 'U+' + selectedCode.toString(16).toUpperCase().padStart(4, '0');
        copyToClipboard(hexStr, `Copied hex code '${hexStr}' to clipboard!`);
      });
    }

    if (inspectorCodeHtml) {
      inspectorCodeHtml.addEventListener('click', () => {
        const item = allRecords[selectedCode];
        if (item) {
          const ent = rec.html(item) ? `&${rec.html(item)};` : `&#${selectedCode};`;
          copyToClipboard(ent, `Copied HTML entity '${ent}' to clipboard!`);
        }
      });
    }

    if (inspectorCodeLatex) {
      inspectorCodeLatex.addEventListener('click', () => {
        const item = allRecords[selectedCode];
        if (item) {
          const cmd = rec.latex(item);
          if (cmd) {
            copyToClipboard(cmd, `Copied LaTeX command '${cmd}' to clipboard!`);
          }
        }
      });
    }

    inspectorFavBtn.addEventListener('click', () => {
      toggleFavorite(selectedCode);
    });

    if (btnToggleInspector) {
      btnToggleInspector.addEventListener('click', () => {
        const isCollapsed = inspectorCard.classList.toggle('is-collapsed');
        inspectorToggleIcon.textContent = isCollapsed ? '+' : '−';
        btnToggleInspector.title = isCollapsed ? 'Expand Inspector' : 'Minimize Inspector';
        try {
          localStorage.setItem('altcode_inspector_collapsed', isCollapsed ? 'true' : 'false');
        } catch (e) {}
      });

      try {
        if (localStorage.getItem('altcode_inspector_collapsed') === 'true') {
          inspectorCard.classList.add('is-collapsed');
          inspectorToggleIcon.textContent = '+';
          btnToggleInspector.title = 'Expand Inspector';
        }
      } catch (e) {}
    }

    // Long press on inspector glyph box to favorite / click to copy
    setupLongPress(inspectorGlyphBox, () => toggleFavorite(selectedCode));
    inspectorGlyphBox.addEventListener('click', () => {
      const item = allRecords[selectedCode];
      if (item) {
        copyToClipboard(rec.glyph(item), `Copied '${rec.glyph(item)}' to clipboard!`);
      }
    });

    // 3. Category Tabs
    categoryTabs.addEventListener('click', (e) => {
      const tab = e.target.closest('.cat-tab');
      if (!tab) return;

      document.querySelectorAll('.cat-tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');

      currentCategory = tab.dataset.cat;
      searchInput.value = '';
      isSearching = false;
      searchClearBtn.style.display = 'none';
      searchModeBadge.style.display = 'none';

      applyFilterAndRender();
    });

    // 4. Range Selector
    rangeSelect.addEventListener('change', (e) => {
      currentRange = e.target.value;
      applyFilterAndRender();
    });

    // 5. Jump to Code Input
    function executeJump() {
      const val = parseInt(jumpInput.value, 10);
      if (!isNaN(val) && val >= 0 && val <= 9999) {
        inspectCharacter(val);
        // Jump range to all or the range containing val
        rangeSelect.value = 'all';
        currentRange = 'all';
        currentCategory = 'all';
        document.querySelectorAll('.cat-tab').forEach((t) => t.classList.remove('active'));
        document.querySelector('.cat-tab[data-cat="all"]').classList.add('active');
        
        applyFilterAndRender();

        setTimeout(() => {
          const row = document.querySelector(`[data-code="${val}"]`);
          if (row) {
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            row.classList.add('is-selected');
          }
        }, 80);
      } else {
        showToast('Please enter a valid code between 0 and 9999');
      }
    }

    btnJump.addEventListener('click', executeJump);
    jumpInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') executeJump();
    });

    // 6. View Switcher (Table vs Grid)
    btnViewTable.addEventListener('click', () => setView('table'));
    btnViewGrid.addEventListener('click', () => setView('grid'));

    // 7. Theme Toggle
    btnTheme.addEventListener('click', toggleTheme);

    // 8. Modals
    btnGuide.addEventListener('click', () => openModal(modalGuide));
    mBtnGuide.addEventListener('click', () => openModal(modalGuide));

    btnInstall.addEventListener('click', handleInstallClick);

    document.querySelectorAll('[data-close]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const modalId = btn.dataset.close;
        const modal = document.getElementById(modalId);
        if (modal) closeModal(modal);
      });
    });

    document.querySelectorAll('.modal-backdrop').forEach((backdrop) => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) closeModal(backdrop);
      });
    });

    // 9. Mobile Bottom Nav actions
    mBtnTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    mBtnSearch.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      searchInput.focus();
    });

    mBtnFavs.addEventListener('click', () => {
      const favTab = document.querySelector('.cat-tab[data-cat="fav"]');
      if (favTab) {
        favTab.click();
        favTab.scrollIntoView({ behavior: 'smooth', inline: 'center' });
      }
    });

    // PWA Install prompt capture
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      btnInstall.style.display = 'inline-flex';
    });

    if (btnTriggerPwa) {
      btnTriggerPwa.addEventListener('click', async () => {
        if (deferredPrompt) {
          deferredPrompt.prompt();
          const { outcome } = await deferredPrompt.userChoice;
          if (outcome === 'accepted') {
            btnInstall.style.display = 'none';
          }
          deferredPrompt = null;
          closeModal(modalInstall);
        }
      });
    }
  }

  // --- View Toggle Handler ---
  function setView(view) {
    currentView = view;
    try {
      localStorage.setItem(STORAGE_KEY_VIEW, view);
    } catch (e) {}

    btnViewTable.classList.toggle('active', view === 'table');
    btnViewGrid.classList.toggle('active', view === 'grid');

    if (view === 'table') {
      tableContainer.style.display = 'block';
      gridContainer.style.display = 'none';
    } else {
      tableContainer.style.display = 'none';
      gridContainer.style.display = 'grid';
    }

    renderFilteredResults();
  }

  function loadViewPreference() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_VIEW);
      if (saved === 'grid' || saved === 'table') {
        setView(saved);
      }
    } catch (e) {}
  }

  // --- Theme Management ---
  function toggleTheme() {
    const isDark = document.body.classList.contains('theme-dark');
    setTheme(isDark ? 'light' : 'dark');
  }

  function setTheme(theme) {
    if (theme === 'light') {
      document.body.classList.remove('theme-dark');
      document.body.classList.add('theme-light');
      themeIcon.textContent = '☀️';
      document.querySelector('meta[name="theme-color"]').setAttribute('content', '#f8fafc');
    } else {
      document.body.classList.remove('theme-light');
      document.body.classList.add('theme-dark');
      themeIcon.textContent = '🌙';
      document.querySelector('meta[name="theme-color"]').setAttribute('content', '#080c14');
    }
    try {
      localStorage.setItem(STORAGE_KEY_THEME, theme);
    } catch (e) {}
  }

  function loadTheme() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_THEME);
      if (saved) {
        setTheme(saved);
      } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        setTheme('light');
      } else {
        setTheme('dark');
      }
    } catch (e) {
      setTheme('dark');
    }
  }

  // --- Clipboard Copy ---
  function copyToClipboard(text, successMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        hapticFeedback();
        showToast(successMsg || `Copied '${text}'!`, 'toast-copy');
      }).catch(() => fallbackCopy(text, successMsg));
    } else {
      fallbackCopy(text, successMsg);
    }
  }

  function fallbackCopy(text, successMsg) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      hapticFeedback();
      showToast(successMsg || `Copied '${text}'!`, 'toast-copy');
    } catch (err) {
      showToast('Could not copy to clipboard');
    }
    document.body.removeChild(textarea);
  }

  // --- Toast Notifications ---
  function showToast(message, extraClass) {
    const toast = document.createElement('div');
    toast.className = `toast ${extraClass || ''}`;
    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'toastOut 200ms forwards';
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 220);
    }, 2500);
  }

  // --- Haptic Feedback ---
  function hapticFeedback() {
    if ('vibrate' in navigator) {
      try {
        navigator.vibrate(40);
      } catch (e) {}
    }
  }

  // --- Modals ---
  function openModal(modal) {
    if (!modal) return;
    modal.style.display = 'flex';
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.style.display = 'none';
  }

  function handleInstallClick() {
    const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const androidContent = document.getElementById('install-android-content');
    const iosContent = document.getElementById('install-ios-content');

    if (isIos) {
      androidContent.style.display = 'none';
      iosContent.style.display = 'block';
    } else {
      androidContent.style.display = 'block';
      iosContent.style.display = 'none';
    }

    openModal(modalInstall);
  }

  // --- Service Worker Registration ---
  function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('./sw.js').then((reg) => {
          console.log('ServiceWorker registered with scope:', reg.scope);
        }).catch((err) => {
          console.log('ServiceWorker registration failed:', err);
        });
      });
    }
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
