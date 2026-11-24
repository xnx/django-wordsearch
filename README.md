# django-wordsearch

The django-wordsearch package adds a word search maker and solver to a Django site. A *word search puzzle* hides a list of words in a grid of letters, each along a straight line of cells, among letters that fill the rest of the grid. The maker hides the words that a visitor enters, in a rectangular or shaped grid, at one of three difficulties, and shows the puzzle with its solution, in which each word is ringed. The solver finds the words in a puzzle that a visitor already has, reading in any of the eight directions.

The package needs Python 3.12 or later and Django 5.2 or later, and has no other dependencies. It stores nothing, so it has no models or migrations. It runs at https://scipython.com/apps/wordsearch/, and its method is described in the blog post [Word search puzzles](https://scipython.com/blog/making-a-word-search-puzzle-in-python/).

## Installation

```bash
pip install django-wordsearch
```

Add the app to `INSTALLED_APPS` and include its URLs:

```python
INSTALLED_APPS = [
    ...,
    "wordsearch",
]
```

```python
urlpatterns = [
    ...,
    path("wordsearch/", include("wordsearch.urls")),
]
```

The maker is then at `wordsearch/` and the solver at `wordsearch/solve/` (the URL names `wordsearch:maker` and `wordsearch:solver`).

## Maker

The maker takes a list of words, one on each line or separated by commas, the numbers of rows and columns, a shape and a difficulty. Spaces and other characters that are not letters are left out of the grid, so that NEW YORK is written NEWYORK. The shapes are a rectangle, a circle (the largest that fits in the grid) and *squares* (the grid with its margin cut away except at its corners). At the easy difficulty, words read right or down; at medium, also diagonally down or up to the right; at hard, in all eight directions, so that words may also read backwards.

The words are placed longest first by a depth-first search: each word is put in the first place where it fits and, if a word fits nowhere, the word before it is moved to its next place. A search that has made twice as many placements as there are words is begun afresh in a new random order, until `WORDSEARCH_TIME_LIMIT`. The other cells are filled with letters drawn at random from the words themselves, in proportion to their frequency in them, so that the filler cannot be told from the words by its letters.

The maker is a GET form, and each puzzle is made with a random seed, so that the link to a puzzle, which holds the seed, makes the same puzzle again. The puzzle and its solution can be downloaded as SVG images, black on white, and a printed page shows only the puzzle and its words.

## Solver

The solver takes a grid, one row on each line, and a list of words. A row's letters may be written together (`SNMEHJU`) or separated by spaces (`S N M E H J U`, as the maker's text output and many printed puzzles have them); a blank cell in a shaped grid is any character that is not a letter, or a space between spaced letters. It finds every occurrence of each word, in all eight directions, rings them on the grid, and lists the row, column and direction of each. A word that reads the same both ways, such as a palindrome, is counted once. The solver is a POST form, since a grid can be too long for an address.

## Settings

| Setting | Default | Meaning |
|---|---|---|
| `WORDSEARCH_MAX_SIZE` | `32` | The greatest number of rows or columns of a puzzle |
| `WORDSEARCH_MAX_WORDS` | `150` | The greatest number of words in a puzzle |
| `WORDSEARCH_MAX_CHARS` | `1500` | The greatest number of characters in a puzzle's list of words |
| `WORDSEARCH_TIME_LIMIT` | `2.0` | The time, in seconds, spent searching for a puzzle before giving up |
| `WORDSEARCH_SOLVER_MAX_SIZE` | `50` | The greatest number of rows or columns of a grid to solve |
| `WORDSEARCH_SOLVER_MAX_WORDS` | `200` | The greatest number of words to find |
| `WORDSEARCH_SOLVER_MAX_CHARS` | `10000` | The greatest number of characters in the grid, and in the words, to solve |
| `WORDSEARCH_RATE_LIMIT_PER_HOUR` | `None` | The puzzles that one visitor may make in an hour, counted in Django's default cache; no limit if `None` |
| `WORDSEARCH_CLIENT_IP` | `None` | The dotted path of a function of the request that returns the visitor's address, for the rate limit; `REMOTE_ADDR` if `None` |

`WORDSEARCH_MAX_CHARS` keeps the address of a puzzle short enough for servers such as gunicorn, which refuses a request line longer than 4094 bytes. Behind a proxy, every visitor has the proxy's `REMOTE_ADDR`, so a site that limits the rate sets `WORDSEARCH_CLIENT_IP` to a function that reads the proxy's header, such as `X-Forwarded-For`.

## Templates and styles

Every page extends `wordsearch/page.html`, which by default is a page of its own. A site overrides it to put the app inside its own pages:

```django
{% extends "base.html" %}
{% block title %}{% block wordsearch_title %}{% endblock %}{% endblock %}
{% block content %}{% block wordsearch_content %}{% endblock %}{% endblock %}
```

The breadcrumb trail starts with `wordsearch/_crumbs_root.html`, and the maker's introduction ends with `wordsearch/_about.html`; both are empty by default, and a site can override them to add its own links.

The app has its own stylesheet, with no dependence on a CSS framework. Its colours follow the page's text colour and `color-scheme` (light or dark), unless the site sets these custom properties on `.wordsearch`: `--wordsearch-ink`, `--wordsearch-muted`, `--wordsearch-line`, `--wordsearch-surface` (the grid's cells), `--wordsearch-input`, `--wordsearch-accent` (links, buttons and the rings of a solution), `--wordsearch-accent-on` and `--wordsearch-page` (behind the grid). The grid's letters are in the page's font.

## Use without Django

The module `wordsearch.puzzle` needs only Python's standard library:

```python
from wordsearch.puzzle import find_words, grid_svg, make_wordsearch

grid, placed = make_wordsearch(["Mercury", "Venus", "Earth", "Mars"], 6, 6, seed=1)
print("\n".join(" ".join(row) for row in grid))
for word, i, j, di, dj in placed:
    print(word, "reads from row", i, "column", j, "in direction", (di, dj))
```

`make_wordsearch` also takes `mask` (`"circle"` or `"squares"`), `difficulty` (`"easy"`, `"medium"` or `"hard"`) and `time_limit`, and raises `ValueError` if the words cannot be fitted. `find_words(grid, words)` returns every occurrence of each word, and `grid_svg(grid, rings, words)` draws a grid as an SVG image.

## Development

The package has its own tests and settings (in `tests/`), independent of any site:

```bash
uv sync --group dev
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

CI runs them with Python 3.12 to 3.14 and Django 5.2 to 6.1, and treats any warning raised in the package's own code, such as of a deprecation, as an error.

To release a new version, change `version` in `pyproject.toml`, add it to `CHANGELOG.md`, commit, and push a tag such as `v0.2.0`. The Release workflow then publishes it to PyPI, by trusted publishing.

## Licence

The django-wordsearch package is licensed under the BSD 3-Clause License (see `LICENSE`).
