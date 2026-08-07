# PSCC Weekly Teaching Plan — UI/UX Improvement Suggestions

**Date:** August 7, 2026
**Target:** `app.py` (Streamlit, three tabs: Timetable View, Data Entry, Weekly Plan View)
**Scope:** Visual design, layout, interaction patterns, feedback, mobile/responsive behavior, accessibility.
**Status:** Recommendations only — no code changes applied.

---

## 1. Current State Summary

The app is functional and well-organized, but it uses Streamlit's default look and a
"form + long list" pattern that gets heavy as data grows. The three biggest UX pain
points today:

1. **Data Entry (Tab 2) is one enormous vertical list** — a teacher with 40 periods
   scrolls past up to 40 text areas with no day grouping, no progress indication, and
   no way to know which entries are new vs. already saved.
2. **Timetable/Plan views are raw `st.dataframe` tables** — no visual hierarchy, no
   highlighting of empty/missing cells, no summary stats, no week context shown in the UI.
3. **No branding or theme** — default Streamlit styling, no page icon, no sidebar, no
   header/footer, mixed button widths.

Everything below is grouped by area, each suggestion with a short explanation of the
problem it solves.

---

## 2. Global / App-Wide Improvements

### 2.1 Add a Streamlit theme (`.streamlit/config.toml`)
- **Problem:** Default Streamlit blue-on-white gives the app no identity and no visual
  separation between sections.
- **Suggestion:** Create `.streamlit/config.toml` with a `[theme]` block — a school/
  college accent color (e.g., dark navy + gold), custom fonts, and consistent
  background/primary colors.
- **Why:** Instant visual cohesion across all three tabs at zero code cost.

### 2.2 Page branding: icon, title, header band
- **Problem:** `st.set_page_config` (app.py:331) sets only a page title; no favicon,
  no logo, no persistent header.
- **Suggestion:** Add a favicon (`page_icon`), and replace the plain `st.title`
  (app.py:332) with an HTML header band (logo/emblem left, college name + app name
  right) using `st.markdown` with inline CSS or `st.html`.
- **Why:** Makes the tool feel like an official college system; also sets the visual
  hierarchy for every tab.

### 2.3 Use the sidebar for global context instead of inline filters
- **Problem:** Class/Section/week filters are inline in each tab, repeating themselves
  and pushing tables down.
- **Suggestion:** Move shared context (current week range, selected class-section) into
  `st.sidebar`; keep tab-specific controls on the page.
- **Why:** Frees vertical space, reduces scrolling, and gives one consistent "where am I
  looking" anchor across tabs.

### 2.4 Consistent button widths
- **Problem:** `use_container_width=True` is used inconsistently — Tab 2/3 download
  buttons are full width (app.py:451, 493), Tab 1's is not (app.py:367).
- **Suggestion:** Standardize: all download buttons full width in `st.columns`, or all
  left-aligned at fixed width.
- **Why:** Visual consistency; users perceive similarly-placed buttons as equally tappable
  (especially on mobile).

### 2.5 Loading / feedback states for slow operations
- **Problem:** `load_entries()` hits the Sheets API on every rerun (app.py:107-116, 405,
  472); while it runs, the UI shows nothing (or a spinner) and users may click again.
- **Suggestion:** Wrap expensive loads in `st.spinner("Loading plans…")`, and/or cache
  entries briefly (e.g., `@st.cache_data(ttl=15)` or session-state timestamped cache) so
  reruns after a save are instant.
- **Why:** Perceived speed and fewer duplicate clicks; also reduces API quota pressure.

### 2.6 Toasts instead of scroll-away messages
- **Problem:** The save success message (app.py:455-457) appears below the Save button —
  good — but other transient feedback would be missed if placed elsewhere.
- **Suggestion:** Use `st.toast()` for short-lived confirmations ("Saved ✔") and reserve
  `st.success` for things that should persist on screen.
- **Why:** Feedback is visible without forcing a scroll position change.

### 2.7 Language-aware web rendering
- **Problem:** Read-only entries render with `st.text()` (app.py:425), which is
  monospace and left-aligned — Urdu/Sindhi Nastaliq script looks cramped and reads
  poorly in the web UI (browser font fallback is inconsistent).
- **Suggestion:** For read-only display, render entries with `st.markdown` using
  `direction: rtl` CSS and a font-family stack (e.g., "Jameel Noori Nastaleeq",
  "Noto Nastaliq Urdu"); or at minimum `st.write()` which wraps better than `st.text`.
- **Why:** Teachers review locked weeks in their own script; correct RTL rendering is a
  correctness issue, not just polish.

### 2.8 Empty states everywhere
- **Problem:** Empty results show a blank table or a bare warning.
- **Suggestion:** Consistent, friendly empty states: an icon + short message + a
  suggested next action (e.g., "No plan submitted yet for this week — ask teachers to
  fill it in Tab 2").
- **Why:** Guides users to the next step instead of leaving them staring at an empty grid.

---

## 3. Tab 1 — Timetable View

### 3.1 Show the full class-section identity, not a concatenated column
- **Problem:** When filtering by Class & Section, the table still shows the combined
  `Class_Section` column (app.py:363), which is now redundant.
- **Suggestion:** Drop `Class_Section` from the table in class mode (show Day/Period/
  Subject/Teacher); keep it only in teacher mode. Show the selection as a page heading
  (e.g., "Timetable — Class 8-B").
- **Why:** Less visual noise; the filter itself already communicates the context.

### 3.2 Group the table by day with visual separators
- **Problem:** 40 rows of the week are one flat table; the eye has to scan for day
  boundaries.
- **Suggestion:** Split the dataframe per day into five/six small tables with day
  headers (e.g., in expanders or day-styled markdown headers), or add a colored Day
  column via `st.column_config`.
- **Why:** Matches how people read a timetable (by day), reduces scan effort.

### 3.3 Make the timetable interactive: search + sort
- **Problem:** The dataframe (app.py:364) is a static dump; no search, no sorting
  control, no column formatting.
- **Suggestion:** Add a text-input filter (search by subject/teacher), and use
  `st.dataframe(..., column_config=...)` to right-align Period, badge Teacher names,
  etc. Enable column sorting via the dataframe's default sort arrows.
- **Why:** Teachers with many periods find their rows faster; admins can answer
  "where does teacher X teach Subject Y?" in one keystroke.

### 3.4 Add a per-day period count / weekly summary line
- **Problem:** No at-a-glance info about the selected timetable.
- **Suggestion:** One `st.caption`/metrics row: "5 days · 40 periods · 8 subjects ·
  6 teachers".
- **Why:** Cheap context that confirms the right class was selected.

### 3.5 Week context for "today"
- **Problem:** No indication of which day is "today" in the timetable.
- **Suggestion:** Bold/highlight the current weekday (and past periods) via
  `st.column_config` text styles or a highlighted badge on the Day cell.
- **Why:** Anchors the reader to the current school day.

---

## 4. Tab 2 — Data Entry (highest-impact area)

### 4.1 Group entries by day (the single biggest win)
- **Problem:** Up to 40 `st.text_area`s stacked vertically (app.py:413-432) with no
  day grouping; teachers lose their place and the page is enormous.
- **Suggestion:** Render one `st.expander` per day ("Monday — 7 periods", …), with the
  day's text areas inside; or a `st.tabs`-per-day layout. Optionally auto-expand the
  first day with unsaved changes.
- **Why:** Cuts perceived length by ~80%, gives day-level structure, and makes partial
  progress visible.

### 4.2 Show save progress: "X of Y periods filled"
- **Problem:** No indication of completion; teachers must visually scan every box.
- **Suggestion:** Add a progress bar or metrics row (e.g., "Filled: 23 / 40") above the
  form, and a colored border/status marker on each text area (empty vs. has content vs.
  changed but unsaved).
- **Why:** Completion is the core motivation of the task; feedback drives finishing it.

### 4.3 Distinguish new / saved / modified entries
- **Problem:** Existing entries load as pre-filled text (app.py:422), so a teacher
  can't tell which slots they've already submitted vs. what's new or unsaved.
- **Suggestion:** Track per-slot status in session state: `(empty | saved | edited-unsaved)`
  and show a small tag next to each label ("saved", "new", "unsaved changes").
- **Why:** Builds trust that the save worked and shows what still needs attention.

### 4.4 Save per day + Save all
- **Problem:** One Save button at the bottom (app.py:435) means an accidental refresh
  loses everything typed; saving requires scrolling to the end.
- **Suggestion:** Keep the full-week "Save week's plan" button, but add a small
  "Save Monday" (etc.) button in each day expander, plus a floating/sticky save bar.
- **Why:** Incremental saves protect against lost work and suit teachers who fill
  plans in bursts.

### 4.5 Confirm before save; feedback after
- **Problem:** No confirmation dialog; a wrong click overwrites the whole week silently
  (upsert overwrites existing rows, app.py:119-142).
- **Suggestion:** On "Save week's plan", show a confirmation step (e.g.,
  `st.dialog`/checkbox: "Overwrite X existing entries?") — or at least a per-row diff
  preview of what changed.
- **Why:** Reduces accidental overwrites — a data-integrity issue as much as a UX one.

### 4.6 Week navigation polish
- **Problem:** Navigation is two buttons ("This week"/"Next week") + a raw date picker
  (app.py:381-390). There's no "Previous week" and no way to jump a term forward.
- **Suggestion:** Add "Previous week" (or a ‹ › pair of week-stepper buttons with a
  label like "Week of 03 Aug — 08 Aug" between them), and keep the date picker only as
  an advanced escape hatch.
- **Why:** Steppers are the mental model ("move a week at a time"); raw date picking is
  error-prone and slower.

### 4.7 "Copy from previous week" action
- **Problem:** Teachers often repeat/continue topics from the prior week; retyping is
  tedious.
- **Suggestion:** Add a "Copy last week's topics" button (with confirmation) that
  pre-fills empty slots from the previous week's entries.
- **Why:** Saves real typing time; a classic win for weekly planning tools.

### 4.8 Character guidance for PDF-truncated cells
- **Problem:** PDF cells truncate at `int(width/1.7)` characters (app.py:246) — long
  topics silently lose text in the exported PDF.
- **Suggestion:** Show a live character counter on each text area ("38/60"), and warn
  (amber) when a topic exceeds the PDF's safe length. (Optionally fix the PDF to wrap
  instead — see doc `improvements_recommended_by_antigravity.md` §4.)
- **Why:** Aligns what teachers type with what the PDF can display, avoiding
  "it's in my entry but not in the report" complaints.

### 4.9 Teacher identity flow
- **Problem:** Teachers pick their name from a dropdown (app.py:400) — easy to pick the
  wrong name and save under someone else.
- **Suggestion:** Until real auth is added (see §6), remember the last selected name in
  session state, show it prominently ("Saving as: Ms. Fatima") next to the Save button,
  and warn if a teacher is viewing entries under a name while entries show another
  submitter.
- **Why:** Reduces misattributed entries; transparency before saving.

### 4.10 RTL text-area support
- **Problem:** Urdu/Sindhi teachers type into LTR text areas; cursor placement and
  alignment are wrong for RTL script.
- **Suggestion:** Set `dir="rtl"` on text areas when the current content (or input
  language) is Urdu/Sindhi via a tiny CSS/styling hook; or let teachers toggle RTL per
  entry.
- **Why:** Typing in Nastaliq with an LTR caret is visibly broken for many users.

---

## 5. Tab 3 — Weekly Plan View (admin)

### 5.1 Highlight empty / unsubmitted cells
- **Problem:** The merged table (app.py:484) looks uniform; missing topics are
  invisible until the user reads the `st.info` count.
- **Suggestion:** Style empty Topic cells (red/amber background or "—" placeholder)
  via `st.column_config` or HTML-styled table, and make the missing count an
  `st.metric` ("Missing: 4/40") instead of prose.
- **Why:** The admin's core question is "what's not done yet" — the UI should answer it
  at a glance.

### 5.2 Show the week range in the UI, not just in the PDF
- **Problem:** The date input (app.py:463) shows one date; the week context
  ("Mon 03 Aug — Sat 08 Aug") only appears in the exported PDF title.
- **Suggestion:** Mirror Tab 2's `st.info` week banner, and add prev/next week stepper
  buttons here too.
- **Why:** Admins browsing multiple weeks need the week context visible without
  exporting.

### 5.3 Add a per-week completion summary
- **Problem:** No stats block.
- **Suggestion:** A metrics row: completion % per class-section, per-subject gaps, count
  of teachers with incomplete weeks.
- **Why:** Turns the view into a monitoring dashboard, not just a table dump.

### 5.4 Teacher filter + grouping
- **Problem:** Admin can only view by class-section; can't isolate one teacher's
  coverage across classes.
- **Suggestion:** Add a "View by teacher" mode in Tab 3 too (reusing Tab 1's pattern).
- **Why:** Same class-section granularity isn't always the right lens for checking
  coverage.

### 5.5 Compare weeks / previous submissions
- **Problem:** No way to see how a week's plan evolved (what changed vs. last week).
- **Suggestion:** A "compare with previous week" toggle that marks changed/unchanged/new
  topics (and relies on `LastUpdated`/`SubmittedBy` for context).
- **Why:** Admins reviewing plan quality and teachers continuing topics both benefit.

---

## 6. Security & Identity (UX-facing side)

- **Problem:** No login; anyone can open the URL, pick any teacher name, and edit
  plans (app.py:400, 435). This is a trust problem for the whole workflow.
- **Suggestion (UI side):** Until proper auth (streamlit-authenticator / Google OAuth,
  per existing doc), add a lightweight "who am I" gate: a name + optional PIN field
  stored in session state, a banner showing the current identity, and a "sign out"
  button. This is explicitly a stop-gap for UX, not real security.
- **Why:** Even light identity framing changes behavior (teachers won't edit under the
  wrong name; admins can spot anonymous use).

---

## 7. Mobile & Accessibility

### 7.1 Verify the app on phone widths
- **Problem:** Text areas and tables are heavy; tabs work but the Data Entry list is
  especially long on mobile.
- **Suggestion:** Test at ~375 px width; enforce `use_container_width` everywhere,
  reduce dataframe height (`height=` param + column config), and consider collapsing
  per-day expanders by default on small screens.
- **Why:** Teachers are most likely to fill plans on phones.

### 7.2 Keyboard / screen-reader pass
- **Problem:** Default Streamlit is decent but custom HTML headers must remain
  accessible.
- **Suggestion:** Keep semantic headings, add `aria-label`s to custom HTML elements,
  and ensure color isn't the only signal for "empty" cells (use text placeholders too).
- **Why:** Inclusive tooling for staff; also cheap to do while styling.

### 7.3 Font size / contrast
- **Problem:** Small 8-9pt PDF and default UI sizes; low contrast for status colors.
- **Suggestion:** Use Streamlit theme variables (`fontSize`), pick accessible palette
  (WCAG AA) for status colors (amber/red/green with text labels).
- **Why:** Readability for a wide age range of staff, plus consistent branding.

---

## 8. PDF Download UX

- **Problem:** Download buttons are named generically and placed in different spots
  with different widths; filenames are good (`Plan_<teacher>_<week>.pdf`) but the
  button doesn't preview the document.
- **Suggestion:** Consistent labeled buttons ("⬇ Download timetable PDF"), a file-size
  caption (e.g., "PDF · 64 KB") under each button, and optionally a collapsible preview
  (`st.download_button` + PDF viewer via `st.components` or link) before download.
- **Why:** Users know what they're getting and can tell the right file apart when
  multiple downloads exist.

---

## 9. Suggested Priority Order

| Priority | Item | Area | Effort |
| :--- | :--- | :--- | :--- |
| 1 | Group Data Entry by day (expanders) | Tab 2 | Low |
| 1 | Progress indicator "X/Y filled" + saved/new tags | Tab 2 | Medium |
| 1 | Week stepper buttons + visible week banner | Tab 2, Tab 3 | Low |
| 1 | Missing-topic highlighting + metric in Tab 3 | Tab 3 | Low |
| 2 | Streamlit theme + favicon + header band | Global | Low |
| 2 | Empty states + toasts + consistent button widths | Global | Low |
| 2 | "Save per day" + confirm-before-overwrite | Tab 2 | Medium |
| 2 | RTL support for Urdu/Sindhi entry & display | Tab 2 | Medium |
| 3 | Timetable search/sort + day grouping + summary | Tab 1 | Medium |
| 3 | Copy-from-previous-week | Tab 2 | Medium |
| 3 | Teacher view in Tab 3 + week comparison | Tab 3 | Medium |
| 4 | Lightweight identity gate (until real auth) | Global | Medium |
| 4 | PDF preview + download labels | All tabs | Low |
| 4 | Mobile pass + accessibility pass | Global | Low |

---

## 10. Notes / Non-Goals

- **Out of scope here:** backend scaling, auth implementation, PDF wrapping fixes,
  caching strategy — these are covered in `improvements_recommended_by_antigravity.md`.
- Several suggestions interact (e.g., day-grouped entry needs the per-slot status
  tracking; the theme affects every other item), so implementing in the priority order
  above avoids rework.
