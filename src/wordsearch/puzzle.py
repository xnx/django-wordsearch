"""Make and solve word search puzzles, in plain Python (no Django).

The words are placed longest first by a depth-first search (backtracking): each
word is put in the first place where it fits and, if a word fits nowhere, the
word before it is moved to its next place. A search is begun afresh, in a new
random order, whenever it has made twice as many placements as there are words,
until a time limit. The other cells are filled with letters drawn from the words,
in proportion to their frequency in them. The method is described in the blog
post "Word search puzzles" (https://scipython.com/blog/making-a-word-search-puzzle-in-python/).
"""

import math
import random
import time
from collections import defaultdict
from html import escape

EMPTY, MASKED = " ", "*"  # a cell not yet filled, and one never to be filled

# The directions in which words may read, as (row step, column step), at each
# difficulty: right and down; also diagonally down and up to the right; and in
# all eight directions, so that words may also read backwards.
DIRECTIONS = {
    "easy": [(0, 1), (1, 0)],
    "medium": [(0, 1), (1, 0), (1, 1), (-1, 1)],
    "hard": [(di, dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if di or dj],
}
DIRECTION_NAMES = {
    (0, 1): "right",
    (0, -1): "left",
    (1, 0): "down",
    (-1, 0): "up",
    (1, 1): "down and right",
    (1, -1): "down and left",
    (-1, 1): "up and right",
    (-1, -1): "up and left",
}


def circle(i, j, nrows, ncols):
    """Whether cell (i, j) lies outside the largest circle that fits in the
    grid."""
    r = min(nrows, ncols) / 2
    return (i + 0.5 - nrows / 2) ** 2 + (j + 0.5 - ncols / 2) ** 2 > r**2


def squares(i, j, nrows, ncols):
    """Whether cell (i, j) lies in the grid's margin but outside the squares
    in its four corners, which overlap the rest of the grid."""
    n = min(nrows, ncols)
    margin, corner = round(0.15 * n), round(0.3 * n)
    in_margin = i < margin or i >= nrows - margin or j < margin or j >= ncols - margin
    in_corner = (i < corner or i >= nrows - corner) and (
        j < corner or j >= ncols - corner
    )
    return in_margin and not in_corner


MASKS = {"circle": circle, "squares": squares}


def letters_only(word):
    """The word as it is written in the grid: in capitals, without spaces,
    hyphens or any other characters that are not letters."""
    return "".join(c for c in word.upper() if c.isalpha())


def fits(grid, word, i, j, di, dj):
    """Whether word can be written in grid from cell (i, j) in direction
    (di, dj): each of its cells must lie in the grid, and be empty or already
    hold the same letter."""
    nrows, ncols = len(grid), len(grid[0])
    for k, letter in enumerate(word):
        r, c = i + k * di, j + k * dj
        if not (0 <= r < nrows and 0 <= c < ncols):
            return False
        if grid[r][c] not in (EMPTY, letter):
            return False
    return True


def placements(grid, word, directions, rng):
    """Generate every placement (i, j, di, dj) of word in grid: the directions
    in random order, and the starting cells in random order for each."""
    nrows, ncols = len(grid), len(grid[0])
    for di, dj in rng.sample(directions, len(directions)):
        starts = [
            (i, j)
            for i in range(nrows)
            for j in range(ncols)
            if fits(grid, word, i, j, di, dj)
        ]
        rng.shuffle(starts)
        for i, j in starts:
            yield i, j, di, dj


class GiveUp(Exception):
    """Raised when a search has tried as many placements as it may."""


def place_words(grid, words, directions, rng, max_steps):
    """Write words into grid by depth-first search: each word in turn is put
    in the first place where it fits and, if a word fits nowhere, the word
    before it is moved to its next place. Return the placements, as tuples
    (word, i, j, di, dj), or None if the words cannot be fitted; raise GiveUp
    after max_steps placements."""
    placed = []
    steps = 0

    def place(k):
        nonlocal steps
        if k == len(words):
            return True
        word = words[k]
        for i, j, di, dj in placements(grid, word, directions, rng):
            steps += 1
            if steps > max_steps:
                raise GiveUp
            cells = [(i + n * di, j + n * dj) for n in range(len(word))]
            before = [grid[r][c] for r, c in cells]
            for (r, c), letter in zip(cells, word, strict=True):
                grid[r][c] = letter
            placed.append((word, i, j, di, dj))
            if place(k + 1):
                return True
            # Undo this placement and try the next.
            placed.pop()
            for (r, c), letter in zip(cells, before, strict=True):
                grid[r][c] = letter
        return False

    return placed if place(0) else None


def make_wordsearch(
    words, nrows, ncols, mask=None, difficulty="medium", seed=None, time_limit=2.0
):
    """Make a word search puzzle of nrows x ncols cells hiding words.

    Return (grid, placed): the grid, a list of rows of letters with MASKED for
    a masked cell, and the placement of each word, (word, i, j, di, dj), which
    reads from cell (i, j) in direction (di, dj). Searches are begun afresh
    until time_limit seconds have passed; raise ValueError if the words have
    not been fitted by then, or cannot be fitted at all."""
    rng = random.Random(seed)
    # Longest first; ties are broken alphabetically, so that a seed always
    # makes the same puzzle.
    words = sorted({letters_only(w) for w in words} - {""}, key=lambda w: (-len(w), w))
    is_masked = MASKS[mask] if mask else lambda *cell: False
    max_steps = 2 * len(words)
    deadline = time.monotonic() + time_limit
    while True:
        grid = [
            [MASKED if is_masked(i, j, nrows, ncols) else EMPTY for j in range(ncols)]
            for i in range(nrows)
        ]
        try:
            placed = place_words(grid, words, DIRECTIONS[difficulty], rng, max_steps)
        except GiveUp:
            if time.monotonic() > deadline:
                raise ValueError(
                    "The words could not be fitted into the grid."
                ) from None
            continue
        if placed is None:
            raise ValueError("The words cannot be fitted into the grid.")
        # Fill the empty cells with letters drawn from the words, in proportion
        # to their frequency in them, so that the filler looks like the words.
        pool = "".join(words)
        for row in grid:
            for j, cell in enumerate(row):
                if cell == EMPTY:
                    row[j] = rng.choice(pool)
        return grid, placed


def parse_grid(text):
    """The grid written in text, one row on each line, as a list of rows of
    capital letters, with MASKED for a blank cell; short rows are padded with
    blank cells. The letters of each row may be separated by single spaces, as
    make_wordsearch.py prints them (with a space for a blank cell), or written
    together, with any character that is not a letter for a blank cell."""
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        return []
    spaced = all(line[k] == " " for line in lines for k in range(1, len(line), 2))
    rows = [line[::2] if spaced else line for line in lines]
    ncols = max(len(row) for row in rows)
    grid = []
    for row in rows:
        cells = []
        for c in row.ljust(ncols):
            letter = c.upper()
            cells.append(letter if c.isalpha() and len(letter) == 1 else MASKED)
        grid.append(cells)
    return grid


def reads(grid, word, i, j, di, dj):
    """Whether word reads from cell (i, j) of grid in direction (di, dj)."""
    nrows, ncols = len(grid), len(grid[0])
    for k, letter in enumerate(word):
        r, c = i + k * di, j + k * dj
        if not (0 <= r < nrows and 0 <= c < ncols) or grid[r][c] != letter:
            return False
    return True


def find_words(grid, words):
    """Every occurrence of each of words in grid, reading in any direction: a
    dictionary of each word's occurrences, as tuples (i, j, di, dj). A word
    that reads the same both ways, such as a palindrome, is counted once."""
    starts = defaultdict(list)
    for i, row in enumerate(grid):
        for j, letter in enumerate(row):
            starts[letter].append((i, j))
    found = {}
    for word in words:
        key = letters_only(word)
        occurrences, seen = [], set()
        directions = DIRECTIONS["hard"] if len(key) > 1 else [(0, 1)]
        for i, j in starts[key[:1]] if key else ():
            for di, dj in directions:
                if reads(grid, key, i, j, di, dj):
                    cells = frozenset((i + k * di, j + k * dj) for k in range(len(key)))
                    if cells not in seen:
                        seen.add(cells)
                        occurrences.append((i, j, di, dj))
        found[word] = occurrences
    return found


def grid_svg(grid, rings=(), words=(), cell=32, label="A word search puzzle"):
    """The grid as an SVG image, in cells cell pixels square, with each ring
    (i, j, di, dj, n), around n letters reading from cell (i, j) in direction
    (di, dj), drawn and, if given, the words to find in columns beneath it.

    The image is black on white, in Verdana, as a file of its own. In a page,
    the stylesheet of this package gives it the page's colours and font through
    the classes of its parts (ws-page, ws-cells, ws-rings, ws-letters and
    ws-words), since CSS rules take precedence over presentation attributes."""
    nrows, ncols = len(grid), len(grid[0])
    pad, size, line = cell / 2, 0.6 * cell, 0.8 * cell
    width, height = ncols * cell + 2 * pad, nrows * cell + 2 * pad
    words = sorted(word.upper() for word in words)
    if words:
        # Columns wide enough for the longest word, as many as fit.
        col_width = 0.65 * size * max(len(word) for word in words) + cell
        ncols_list = max(1, int((width - 2 * pad) // col_width))
        nlines = math.ceil(len(words) / ncols_list)
        height += nlines * line + pad
    font = 'font-family="Verdana, Arial, sans-serif"'
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}"'
        f' width="{width:g}" height="{height:g}" role="img"'
        f' aria-label="{escape(label)}">',
        '<rect class="ws-page" width="100%" height="100%" fill="white"/>',
    ]
    # The unmasked cells, as one path, so that the shape of a mask can be seen.
    cells = "".join(
        f"M{pad + j * cell:g} {pad + i * cell:g}h{cell}v{cell}h-{cell}z"
        for i, row in enumerate(grid)
        for j, letter in enumerate(row)
        if letter != MASKED
    )
    svg.append(f'<path class="ws-cells" d="{cells}" fill="white"/>')
    # A ring around each word: a rectangle with semicircular ends, drawn along
    # the line through the centres of its first and last letters.
    svg.append('<g class="ws-rings" fill="none" stroke="#0e5587" stroke-width="2.5">')
    r = 0.4 * cell
    for i, j, di, dj, n in rings:
        x0, y0 = pad + (j + 0.5) * cell, pad + (i + 0.5) * cell
        length = (n - 1) * cell * math.hypot(di, dj)
        angle = math.degrees(math.atan2(di, dj))
        svg.append(
            f'<rect x="{x0 - r:g}" y="{y0 - r:g}" width="{length + 2 * r:g}"'
            f' height="{2 * r:g}" rx="{r:g}"'
            f' transform="rotate({angle:g} {x0:g} {y0:g})"/>'
        )
    svg.append("</g>")
    # Each letter is centred in its cell: its baseline lies 0.35 em below the
    # cell's centre, about half the height of a capital letter.
    svg.append(
        f'<g class="ws-letters" fill="black" {font} font-size="{size:g}"'
        ' font-weight="600" text-anchor="middle">'
    )
    for i, row in enumerate(grid):
        for j, letter in enumerate(row):
            if letter != MASKED:
                x, y = pad + (j + 0.5) * cell, pad + (i + 0.5) * cell
                svg.append(
                    f'<text x="{x:g}" y="{y + 0.35 * size:g}">{escape(letter)}</text>'
                )
    svg.append("</g>")
    if words:
        svg.append(f'<g class="ws-words" fill="black" {font} font-size="{size:g}">')
        for k, word in enumerate(words):
            x = pad + (k // nlines) * col_width
            y = nrows * cell + 2 * pad + (k % nlines + 0.75) * line
            svg.append(f'<text x="{x:g}" y="{y:g}">{escape(word)}</text>')
        svg.append("</g>")
    svg.append("</svg>")
    return "\n".join(svg)
