# Phase 3: Frontend Platform Abstraction & Dynamic UI

**Goal:** Eliminate hardcoded "LinkedIn" references and static category labels in the frontend. Make the UI driven by business config via a new `/api/config` endpoint.

**Prerequisite:** Phase 1 complete (business_config.json exists)
**Estimated effort:** 2-3 hours
**Impact:** Platform swap (LinkedIn -> Instagram, Twitter/X, blog) becomes a config change. Category labels are dynamic. Eliminates all 10 platform coupling points and 6 content category coupling points.

---

## Context

After Phase 1, the backend reads from `business_config.json`. But the frontend (`templates/index.html`) still has:
- 6 hardcoded "LinkedIn" references in scheduling/copy UI
- 4 hardcoded category buttons with static labels and placeholders
- 10 hardcoded feed category dropdown options
- "EST" timezone hardcoded in scheduling text
- A hardcoded `window.open('https://linkedin.com/feed')` call

This phase makes the frontend config-driven by:
1. Adding an API endpoint that exposes relevant business config to the frontend
2. Replacing hardcoded strings with JavaScript variables populated from that config
3. Making category buttons and feed category dropdowns dynamic

---

## Step 1: Add `/api/config` endpoint

**Edit file:** `signal-and-stance/app.py`

Add a new route that exposes the business config subset relevant to the frontend. This should NOT expose sensitive data (no API keys, no scoring internals).

Add this route near the top of the routes section (after the index route):

```python
from business_config import BUSINESS, APP_NAME

@app.route("/api/config")
def get_config():
    """Return business config for frontend use."""
    return {
        "app_name": APP_NAME,
        "owner": {
            "name": BUSINESS["owner"]["name"],
            "business": BUSINESS["owner"]["business"],
        },
        "platform": {
            "name": BUSINESS["platform"]["name"],
            "scheduling_url": BUSINESS["platform"]["scheduling_url"],
        },
        "content": {
            "categories": BUSINESS["content"]["categories"],
            "carousel_templates": BUSINESS["content"]["carousel_templates"],
        },
        "schedule": {
            "timezone": BUSINESS["schedule"]["timezone"],
        },
        "feeds": {
            "categories": BUSINESS["feeds"]["categories"],
        },
    }
```

---

## Step 2: Load config in frontend JavaScript

**Edit file:** `signal-and-stance/templates/index.html`

Add a config loading function near the top of the `<script>` section, before other JavaScript code. The app should fetch `/api/config` on page load and store it globally.

Find the opening `<script>` tag and add this immediately after:

```javascript
// Business config — loaded from backend on page load
let APP_CONFIG = null;

async function loadConfig() {
    try {
        const resp = await fetch('/api/config');
        APP_CONFIG = await resp.json();
        applyConfig();
    } catch (e) {
        console.error('Failed to load config:', e);
        // Fallback defaults
        APP_CONFIG = {
            app_name: 'Signal & Stance',
            platform: { name: 'LinkedIn', scheduling_url: 'https://linkedin.com/feed' },
            content: { categories: {} },
            schedule: { timezone: 'EST' },
            feeds: { categories: {} },
        };
    }
}

function applyConfig() {
    // Update page title
    document.title = APP_CONFIG.app_name;

    // Update all elements with data-app-name attribute
    document.querySelectorAll('[data-app-name]').forEach(el => {
        el.textContent = APP_CONFIG.app_name;
    });

    // Update all elements with data-platform-name attribute
    document.querySelectorAll('[data-platform-name]').forEach(el => {
        el.textContent = el.textContent.replace(/LinkedIn/g, APP_CONFIG.platform.name);
    });
}
```

Call `loadConfig()` in the page's initialization:

```javascript
// At the bottom of the script section, in the DOMContentLoaded handler or equivalent:
loadConfig();
```

---

## Step 3: Replace hardcoded "LinkedIn" references

**Edit file:** `signal-and-stance/templates/index.html`

There are 6 LinkedIn-specific strings to make dynamic. For each one:

### 3a. Scheduling status text (line ~1461)

Find:
```javascript
'Scheduled for ' + (slot.scheduled_time || slot.suggested_time) + ' EST on LinkedIn'
```

Replace with:
```javascript
'Scheduled for ' + (slot.scheduled_time || slot.suggested_time) + ' ' + (APP_CONFIG?.schedule?.timezone || 'EST') + ' on ' + (APP_CONFIG?.platform?.name || 'LinkedIn')
```

### 3b. "Copy & Schedule on LinkedIn" button (line ~1500)

Find the button text "Copy & Schedule on LinkedIn" and replace with a dynamic version:

```html
<button onclick="copyAndSchedule()" id="copy-schedule-btn">
    Copy & Schedule on <span data-platform-name>LinkedIn</span>
</button>
```

### 3c. Cancel scheduling text (line ~1549)

Find "cancel the scheduled post on LinkedIn" and replace:

```javascript
`cancel the scheduled post on ${APP_CONFIG?.platform?.name || 'LinkedIn'}`
```

### 3d. Open platform URL (line ~1762)

Find:
```javascript
window.open('https://linkedin.com/feed', '_blank');
```

Replace with:
```javascript
window.open(APP_CONFIG?.platform?.scheduling_url || 'https://linkedin.com/feed', '_blank');
```

### 3e. Paste instruction (line ~1781)

Find "Paste your post on LinkedIn, then use the clock icon to schedule it" and replace:

```javascript
`Paste your post on ${APP_CONFIG?.platform?.name || 'LinkedIn'}, then use the clock icon to schedule it`
```

### 3f. Feed category "LinkedIn" option (lines ~208, ~235)

These are in the feed category dropdown. They'll be replaced entirely in Step 5 (dynamic dropdown).

---

## Step 4: Make category buttons dynamic

**Edit file:** `signal-and-stance/templates/index.html`

The current category buttons (around lines 54-73) are hardcoded HTML:

```html
<button class="category-btn" data-category="pattern">Pattern</button>
<button class="category-btn" data-category="faq">FAQ</button>
<button class="category-btn" data-category="noticed">Noticed</button>
<button class="category-btn" data-category="hottake">Hot Take</button>
```

Replace with a container that gets populated from config:

```html
<div id="category-buttons" class="category-buttons">
    <!-- Populated from config -->
</div>
```

Add JavaScript to populate:

```javascript
function renderCategoryButtons() {
    const container = document.getElementById('category-buttons');
    if (!APP_CONFIG?.content?.categories) return;

    container.innerHTML = '';
    for (const [key, cat] of Object.entries(APP_CONFIG.content.categories)) {
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.dataset.category = key;
        btn.textContent = cat.label;
        btn.title = cat.placeholder;
        btn.addEventListener('click', () => selectCategory(key));
        container.appendChild(btn);
    }
}
```

Update `applyConfig()` to call `renderCategoryButtons()`.

Also update the textarea placeholder to be dynamic. When a category is selected, set the placeholder from config:

```javascript
function selectCategory(category) {
    // ... existing selection logic ...

    // Update placeholder from config
    const catConfig = APP_CONFIG?.content?.categories?.[category];
    if (catConfig) {
        document.getElementById('raw-input').placeholder = catConfig.placeholder;
    }
}
```

---

## Step 5: Make feed category dropdown dynamic

**Edit file:** `signal-and-stance/templates/index.html`

The feed category dropdowns (around lines 200-213 and 229-240) have hardcoded `<option>` elements. Replace with a dynamic approach.

Replace the static options with an empty select that gets populated:

```html
<select id="feed-category-filter" class="feed-category-select">
    <option value="">All Categories</option>
    <!-- Populated from config -->
</select>
```

Add JavaScript:

```javascript
function renderFeedCategoryDropdowns() {
    if (!APP_CONFIG?.feeds?.categories) return;

    const selects = document.querySelectorAll('.feed-category-select');
    selects.forEach(select => {
        // Preserve the first "All" option
        const firstOption = select.querySelector('option');

        select.innerHTML = '';
        if (firstOption) select.appendChild(firstOption);

        for (const [key, description] of Object.entries(APP_CONFIG.feeds.categories)) {
            const opt = document.createElement('option');
            opt.value = key;
            // Capitalize first letter of each word for display
            opt.textContent = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            opt.title = description;
            select.appendChild(opt);
        }
    });
}
```

Update `applyConfig()` to call `renderFeedCategoryDropdowns()`.

---

## Step 6: Update the category display map

**Edit file:** `signal-and-stance/templates/index.html`

Around line 2070, there's a JavaScript object mapping category keys to display names:

```javascript
const categoryMap = {
    'leadership': 'Leadership',
    'careers': 'Careers',
    'executive_careers': 'Executive Careers',
    'hr_recruiting': 'HR/Recruiting',
    'labor_data': 'Labor Data',
    'linkedin': 'LinkedIn',
    'hr_tech': 'HR Tech',
    'compensation': 'Compensation',
    'workplace': 'Workplace',
    'business_news': 'Business News',
};
```

Replace with a dynamic function:

```javascript
function getCategoryDisplayName(key) {
    // Try to get from config first
    if (APP_CONFIG?.feeds?.categories?.[key]) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }
    // Fallback: capitalize the key
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
```

Update all references to `categoryMap[key]` to use `getCategoryDisplayName(key)`.

---

## Step 7: Update the `contentTypeToCat` mapping

**Edit file:** `signal-and-stance/templates/index.html`

Around line 296-302, there's a mapping from content schedule types to generation categories:

```javascript
const contentTypeToCat = {
    'Educational / Pattern': 'pattern',
    'Tactical Tip': 'faq',
    'Deep Dive / Story': 'noticed',
    'Thought Leadership / Hot Take': 'hottake',
    'Quick Win / Encouragement': 'pattern',
};
```

This mapping needs to stay functional but should be documented as config-dependent. Add a comment:

```javascript
// Maps CONTENT_SCHEDULE types (from business_config.json schedule.days.*.content_type)
// to content category keys (from business_config.json content.categories).
// Update this mapping if you change content types or categories in business_config.json.
const contentTypeToCat = {
    'Educational / Pattern': 'pattern',
    'Tactical Tip': 'faq',
    'Deep Dive / Story': 'noticed',
    'Thought Leadership / Hot Take': 'hottake',
    'Quick Win / Encouragement': 'pattern',
};
```

**Future improvement (out of scope for this phase):** Move this mapping into `business_config.json` and expose it via `/api/config`. For now, the comment is sufficient.

---

## Step 8: Update the `applyConfig()` function

Consolidate all the dynamic rendering into the `applyConfig()` function:

```javascript
function applyConfig() {
    if (!APP_CONFIG) return;

    // Update page title
    document.title = APP_CONFIG.app_name;

    // Update app name in headers
    document.querySelectorAll('[data-app-name]').forEach(el => {
        el.textContent = APP_CONFIG.app_name;
    });

    // Render dynamic UI components
    renderCategoryButtons();
    renderFeedCategoryDropdowns();
}
```

---

## Verification Checklist

- [ ] `curl http://localhost:5000/api/config` returns JSON with app_name, owner, platform, content, schedule, feeds
- [ ] Page title shows app name from config (not hardcoded)
- [ ] H1 headers show app name from config
- [ ] Category buttons are generated from config (correct labels and placeholders)
- [ ] Feed category dropdowns are populated from config
- [ ] "Copy & Schedule on LinkedIn" button shows platform name from config
- [ ] Scheduling status shows timezone from config
- [ ] "Open LinkedIn" button opens the URL from config
- [ ] Paste instruction references platform name from config
- [ ] All existing functionality still works (generating, scheduling, browsing)
- [ ] Change `platform.name` to "Instagram" in business_config.json and verify all UI strings update

---

## What This Phase Achieves

**Before:** 16 coupling points in the frontend (10 platform + 6 category). Changing the platform or categories requires editing HTML.

**After:** Frontend is config-driven. Platform name, scheduling URL, timezone, category labels, and feed categories all come from `/api/config`. Swapping platform or categories is a `business_config.json` edit.

**Remaining after all 3 phases:**
- Authored content in prompt files (voice rules, examples, content arcs) — these require manual creative work per business domain
- The `DEFAULT_FEEDS` list in `feeds.py` — these are domain-specific content sources
- CSS color variables — these could be made config-driven but are low priority

---

## Files Modified
- `signal-and-stance/app.py` (add `/api/config` route)
- `signal-and-stance/templates/index.html` (dynamic categories, platform references, config loading)

## Files NOT Modified (no changes needed)
- `signal-and-stance/static/style.css` (already uses CSS variables, domain-agnostic)
- `signal-and-stance/database.py` (already domain-agnostic)
- `signal-and-stance/schema.sql` (already domain-agnostic)
