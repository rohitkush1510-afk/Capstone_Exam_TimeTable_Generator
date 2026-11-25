# Exam Timetable Generator

A small, dependency-free project that builds an exam timetable from student subject lists. It guarantees that **no student has two exams in the same time slot**, and finds the **minimum possible number of slots** rather than just any valid schedule.

The project ships two front ends for the same idea:

- a **Python command-line tool** (`src/`)
- a **standalone browser dashboard** (`dashboard/index.html`)

---

## Table of contents

1. [The problem](#1-the-problem)
2. [Mapping the problem to graph coloring](#2-mapping-the-problem-to-graph-coloring)
3. [Project structure](#3-project-structure)
4. [Getting started](#4-getting-started)
5. [Command-line usage](#5-command-line-usage)
6. [Browser dashboard usage](#6-browser-dashboard-usage)
7. [The algorithm in detail](#7-the-algorithm-in-detail)
8. [Module API reference](#8-module-api-reference)
9. [Design system](#9-design-system)
10. [Limitations and differences](#10-limitations-and-differences)
11. [Ideas for extension](#11-ideas-for-extension)

---

## 1. The problem

Given a list of students and the subjects they take, assign every subject to a time slot such that:

- if two subjects are taken by the **same student**, they must be in **different** slots;
- the number of distinct slots used is **as small as possible**.

The second requirement is what makes this interesting: a naive greedy assignment often uses more slots than necessary. This project searches until it can prove that no smaller number of slots works.

---

## 2. Mapping the problem to graph coloring

Graph coloring is the classic abstraction for this:

| Timetable concept | Graph concept |
| --- | --- |
| Subject | Vertex (node) |
| Two subjects shared by a student | Edge (conflict) |
| Time slot | Color |
| Minimum number of slots | Chromatic number |

The rule is simple: **adjacent vertices may not share a color.** In timetable terms, subjects that conflict never land in the same slot.

---

## 3. Project structure

```
.
├── src/
│   ├── __init__.py     # marks src as a package
│   ├── graph.py        # CSV loading + conflict graph construction
│   ├── coloring.py     # backtracking solver for the minimum coloring
│   └── main.py         # terminal entry point / report printer
├── dashboard/
│   └── index.html      # browser UI: markup + CSS + its own JS solver
├── data/
│   └── sample.csv      # example students and subjects
└── README.md
```

### File responsibilities

| File | What it does |
| --- | --- |
| `src/graph.py` | Reads the CSV (`load_students`), builds `{subject: set(conflicts)}` (`build_conflict_graph`) |
| `src/coloring.py` | Checks color safety (`is_safe`), recurses (`backtrack_color`), and finds the minimum `k` (`find_min_slots`) |
| `src/main.py` | Reads an optional path argument, runs the pipeline, prints the graph and timetable |
| `dashboard/index.html` | Parses text input, runs an equivalent JavaScript solver, renders stats, badges, a chart and slot chips |
| `data/sample.csv` | Seven students covering six subjects — the sample needs four slots |

---

## 4. Getting started

**Requirements:** Python 3 for the CLI (standard library only: `csv`, `itertools`, `sys`). Any modern browser for the dashboard. No packages, servers or build step are needed.

Both entry points work directly after cloning/downloading the folder.

---

## 5. Command-line usage

Run from the project root, because the default input path is relative:

```bash
python src/main.py                 # uses data/sample.csv
python src/main.py data/mine.csv   # custom CSV path
```

### CSV format

One student per row, with a `student` column and a `subjects` column. Subjects in a row are separated by semicolons:

```csv
student,subjects
Asha,Math;Physics;English
Ravi,Math;Chemistry
Meera,Physics;Biology
Kiran,Chemistry;Biology;Math
Divya,English,Biology
Arjun,Math;English;History
Sara,Physics;History
```

(The `Divya` line above intentionally shows the wrong separator — use `;` as in `data/sample.csv`. With `,`, everything after `English` becomes part of one subject name.)

### Parsing behavior

- Whitespace around names and subjects is stripped.
- Empty subjects are ignored.
- Duplicate students: the **last row wins** (the dictionary key is overwritten).
- Duplicate subjects within one student are harmless: the graph builder converts the list to a `set` before creating pairs.
- Missing `student` or `subjects` columns raise a `KeyError`; there is no CSV validation layer.

### Example output

```
=== Conflict Graph ===
  Biology      conflicts with: ['Chemistry', 'English', 'Math', 'Physics']
  Chemistry    conflicts with: ['Biology', 'Math']
  English      conflicts with: ['Biology', 'History', 'Math', 'Physics']
  History      conflicts with: ['English', 'Math', 'Physics']
  Math         conflicts with: ['Biology', 'Chemistry', 'English', 'History', 'Physics']
  Physics      conflicts with: ['Biology', 'English', 'History', 'Math']

=== Minimum time slots needed: 4 ===

  Slot 1: Math
  Slot 2: Biology, History
  Slot 3: Chemistry, English
  Slot 4: Physics
```

`main.py` prints subjects in the sorted order produced by `build_conflict_graph()`; the dashboard additionally sorts subjects alphabetically inside each slot.

---

## 6. Browser dashboard usage

Open `dashboard/index.html` directly in a browser (double-click it, or open `file:///path/to/dashboard/index.html`).

### Input format

One student per line, in `Name: Subject1, Subject2` form:

```
Asha: Math, Physics, English
Ravi: Math, Chemistry
Meera: Physics, Biology
```

The sample is pre-filled and solved automatically on page load.

### Controls

| Control | Behavior |
| --- | --- |
| **Generate Timetable** | Parses the textarea, solves, and renders the result |
| **Load sample** | Restores the built-in seven-student sample and solves it |
| **Clear** | Empties the input, hides errors, resets the result panel |

### Output sections

1. **Error box** — shown when a line is missing `:` or has no student name. Parsing continues with the valid lines.
2. **Summary badges** — `k` time slots (pink→red), `Valid schedule` (cyan→blue), subject count.
3. **Stats** — time slots, subjects, students and conflict edges (4 cards).
4. **Exams per slot chart** — an SVG bar chart whose bars use the `growBar` animation.
5. **Slots** — one glass panel per slot with subject chips; chip colors cycle through a 10-color palette.

Subject names are escaped with `escapeHTML()` before being inserted into the DOM, so input like `<img src=x onerror=...>` is displayed as text rather than executed.

---

## 7. The algorithm in detail

### Data flow

```
input (CSV or textarea)
        │
        ▼
{student: [subject, ...]}
        │
        ▼
{subject: set(conflicting subjects)}
        │
        ▼
try k = 1, 2, 3, ...
        │
        ▼
backtrack(order, graph, colors, k)
        │
        ▼
{k, {subject: slot}}  ──► grouped slots ──► CLI output / dashboard UI
```

### Step 1 — Build the conflict graph

For each student, take every **pair** of subjects they take and add an edge both ways:

```python
for subs in students.values():
    for a, b in combinations(set(subs), 2):
        graph[a].add(b)
        graph[b].add(a)
```

The JavaScript version uses the equivalent nested loop over `subs`. The resulting graph is undirected and stored as an adjacency set per subject.

For the bundled sample: 6 subjects, 11 conflict edges.

### Step 2 — Order the vertices

```python
order = sorted(subjects, key=lambda s: len(graph[s]), reverse=True)
```

Subjects with the most conflicts are colored first. This is a heuristic: it makes invalid partial colorings fail early, dramatically pruning the search without affecting correctness.

For the sample, `Math` (5 conflicts) goes first, then `Biology`, `English`, `Physics` (4 each), `History` (3) and `Chemistry` (2).

### Step 3 — Backtracking search (DFS)

```python
def backtrack_color(order, graph, colors, index, max_colors):
    if index == len(order):
        return True                     # every subject colored legally

    subject = order[index]
    for color in range(1, max_colors + 1):
        if is_safe(subject, color, graph, colors):
            colors[subject] = color     # CHOOSE
            if backtrack_color(order, graph, colors, index + 1, max_colors):
                return True             # SUCCESS
            del colors[subject]         # UNDO (backtrack)

    return False                        # dead end — caller tries another color
```

`is_safe()` rejects a color if any neighbor already uses it:

```python
def is_safe(subject, color, graph, colors):
    return all(colors.get(neighbor) != color for neighbor in graph[subject])
```

Key properties:

- `colors` is mutated in place and undone on failure, so each recursive branch gets a clean state.
- Returning `True` unwinds immediately; the first complete coloring found for a given `k` is returned.
- Search order is colors `1..k`, so slot numbering is stable.

### Step 4 — Find the minimum

```python
for k in range(1, len(subjects) + 1):
    colors = {}
    if backtrack_color(order, graph, colors, 0, k):
        return k, colors
```

Trying `k` in increasing order means the first successful `k` is**optimal**: if `k - 1` had been possible, the loop would have stopped there. With the sample it stops at `k = 4`.

### Correctness and complexity

- **Correctness:** the safety check enforces the edge constraint at every assignment, so every returned coloring is valid. Increasing `k` guarantees minimality.
- **Complexity:** deciding colorability is NP-complete. For a fixed `k`, the search is at most `k^V` (V = subjects); with up to V values of `k` tried, the worst case is roughly `O(V · k^V)`. Graph construction is `O(S · M²)` for S students with at most M subjects each.
- **Practicality:** real inputs here are small (the sample has 6 subjects), so the exhaustive search is instantaneous. The degree ordering is what keeps larger inputs tolerable.

---

## 8. Module API reference

### `src/graph.py`

| Function | Signature | Returns |
| --- | --- | --- |
| `load_students` | `load_students(path)` | `{student_name: [subject, ...]}` from a CSV with `student` / `subjects` columns |
| `build_conflict_graph` | `build_conflict_graph(students)` | `(subjects, graph)` where `subjects` is a sorted list and `graph` maps each subject to a `set` of conflicts |

### `src/coloring.py`

| Function | Signature | Returns / effect |
| --- | --- | --- |
| `is_safe` | `is_safe(subject, color, graph, colors)` | `True` if no neighbor already has that color |
| `backtrack_color` | `backtrack_color(order, graph, colors, index, max_colors)` | `True` when a full coloring is found; mutates `colors`, undoing failed choices |
| `find_min_slots` | `find_min_slots(subjects, graph)` | `(k, {subject: slot_number})` for the smallest workable `k` |

### `src/main.py`

`main()` chooses `sys.argv[1]` or `data/sample.csv`, runs the pipeline and prints the conflict graph, minimum slot count, and subjects grouped by slot.

### `dashboard/index.html` (JavaScript)

| Function | Purpose |
| --- | --- |
| `parse(text)` | Splits lines on `:`, trims, deduplicates subjects, collects error messages |
| `buildGraph(students)` | Builds the adjacency-`Set` graph |
| `safe(sub, color, graph, colors)` | Same constraint check as `is_safe` |
| `backtrack(order, graph, colors, i, k)` | Same DFS backtracking |
| `findMin(graph)` | Same increasing-`k` search |
| `escapeHTML(s)` | Escapes `& < > " '` before HTML insertion |
| `run()` | Orchestrates parsing, solving and rendering (stats, badges, chart, slots) |
| `loadSample()` / `clearAll()` | Button handlers |

---

## 9. Design system

The dashboard stylesheet is **layered**: the original light-theme rules remain at the top of the `<style>` block, and a later design-system layer repoints the same custom properties and adds new rules. Nothing from the original CSS was deleted.

### Tokens

| Token | Value | Used for |
| --- | --- | --- |
| `--bg` | `#0f172a` | Page background (set on `html`) |
| `--card` / surface | `rgba(17, 24, 39, 0.6)` | Glass panels |
| `--primary` | `#667eea` | Brand blue, buttons, links |
| `--primary-dark` / `--secondary` | `#764ba2` | Brand purple, gradient end |
| `--success` | `#4facfe` | Success gradient / code text |
| `--warning` | `#fee140` | Warning accent |
| `--danger` | `#f5576c` | Error box and danger gradient |
| `--glass-blur` | `16px` | `backdrop-filter` on panels |
| `--border` | `rgba(255, 255, 255, 0.08)` | Panel borders at rest |
| `--border-hover` | `rgba(255, 255, 255, 0.2)` | Panel borders on hover |
| `--glass-shadow` | `0 4px 30px rgba(0, 0, 0, 0.1)` | Subtle panel depth |
| `--font` | `'Cairo', system-ui, …` | Body and headings |
| `--font-data` | monospace stack | Numbers and code |

### Glass panels

`header`, `.card`, `.stat` and `.slot` share one rule set: translucent surface, `backdrop-filter: blur(16px)`, a semi-transparent white border, 16px radius and the soft shadow. On hover they lift by 5px, brighten the border to `0.2` alpha and deepen the shadow.

### Typography

Cairo is loaded from Google Fonts at the top of the stylesheet with a system-font fallback for offline use. Headers are bold and range from 1.25rem (card titles) to 1.875rem (page title); body text is 0.875rem in slate-300 (`#cbd5e1`); numbers use a monospace stack with tabular numerals.

### Animations

| Name | Effect | Duration / timing |
| --- | --- | --- |
| `blob` | Background gradient blobs scale `0.9 → 1.1` while drifting | 7s ease-in-out, infinite alternate (second blob offset by −3.5s) |
| `slide-up` | Entrance from `translateY(20px)` + opacity 0 to rest | 0.6s ease-out, staggered per panel/stat/slot |
| `growBar` | SVG bars scale `scaleY(0) → scaleY(1)` from the baseline | 0.8s ease-out, applied via `.grow-bar` |

`prefers-reduced-motion: reduce` collapses all animation and transition durations to `0.01ms`. Logical properties (`inset-inline-start`, `margin-inline`, etc.) and an `[dir='rtl']` helper make the layout RTL-ready; add `dir="rtl"` to `<html>` to enable it.

### Result-specific accents

- `.badge--high` uses a pink→red gradient (`#ec4899 → #f5576c`) for the primary result ("N time slots").
- `.badge--success` uses a cyan→blue gradient (`#22d3ee → #4facfe`) for the "Valid schedule" badge.
- The chart's bars use the brand blue→purple gradient.

---

## 10. Limitations and differences

- **Two independent implementations.** The Python solver and the dashboard JavaScript implement the same algorithm but do not share code; a change to one must be mirrored in the other.
- **Different input formats.** CLI: CSV with semicolon-separated subjects. Dashboard: `Name: A, B` lines. Neither accepts the other's format.
- **No persistence.** Nothing is saved; refresh resets the dashboard to the sample, and the CLI only prints to stdout.
- **Minimal validation.** The CLI assumes correct headers and will raise on malformed CSV. The dashboard checks for a missing `:` and empty names but silently overwrites duplicate student names.
- **Color cycling.** The dashboard uses a 10-color chip palette; more than 10 slots reuses colors, so chip color alone does not uniquely identify a slot.
- **Slot contents differ in ordering.** The CLI preserves the sorted subject order; the dashboard sorts subjects alphabetically within each slot.
- **Exponential worst case.** Very large subject sets can make exact minimum-coloring slow; the current design targets classroom-sized inputs.

---

## 11. Ideas for extension

- Share one solver between both front ends (e.g. compile the Python logic to an API the dashboard calls).
- Add constraint types: preferred rooms, unavailable slots, or maximum exams per slot.
- Add greedy/DSATUR upper bound to prune the `k` search further.
- Export the timetable to CSV, JSON or a printable page.
- Add unit tests for parsing, graph construction and known-optimal cases.
- Persist input in `localStorage` in the dashboard and add an RTL toggle button.
