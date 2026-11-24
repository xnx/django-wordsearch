"""The maker and the solver."""

import base64
import re
import secrets
from urllib.parse import urlencode

from django.core.cache import cache
from django.shortcuts import render

from . import puzzle
from .conf import client_ip, setting

MASK_CHOICES = [("", "Rectangle"), ("circle", "Circle"), ("squares", "Squares")]
DIFFICULTY_CHOICES = [
    ("easy", "Easy: words read right or down"),
    ("medium", "Medium: also diagonally, down or up to the right"),
    ("hard", "Hard: in any direction, including backwards"),
]


def words_in(text):
    """The words in text, one on each line or separated by commas, each once."""
    words = (word.strip() for word in re.split(r"[\r\n,]", text))
    return list(dict.fromkeys(word for word in words if word))


def svg_data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def rate_limited(request):
    """Count a puzzle made for this visitor; True once over the hourly limit."""
    limit = setting("RATE_LIMIT_PER_HOUR")
    if limit is None:
        return False
    key = f"wordsearch:rate-limit:{client_ip(request)}"
    cache.add(key, 0, timeout=60 * 60)
    try:
        made = cache.incr(key)
    except ValueError:  # expired since add()
        made = 1
    return made > limit


def maker_problem(form, words):
    """What is wrong with the maker's form, or None; on success, form gets the
    grid's numbers of rows and columns as ints."""
    max_size = setting("MAX_SIZE")
    try:
        nrows, ncols = int(form["rows"]), int(form["cols"])
    except ValueError:
        return "Please give the numbers of rows and columns as whole numbers"
    if not (2 <= nrows <= max_size and 2 <= ncols <= max_size):
        return f"The grid may have from 2 to {max_size} rows and columns"
    if form["mask"] and form["mask"] not in puzzle.MASKS:
        return "Please choose one of the shapes listed"
    if form["difficulty"] not in puzzle.DIRECTIONS:
        return "Please choose one of the difficulties listed"
    if len(form["words"]) > setting("MAX_CHARS"):
        return f"The words may have at most {setting('MAX_CHARS')} characters in all"
    if len(words) > setting("MAX_WORDS"):
        return f"Please give at most {setting('MAX_WORDS')} words"
    for word in words:
        if len(puzzle.letters_only(word)) < 2:
            return f"{word} has fewer than two letters"
        if len(puzzle.letters_only(word)) > max(nrows, ncols):
            return f"{word} has too many letters for the grid"
    form.update(nrows=nrows, ncols=ncols)
    return None


def maker(request):
    """Make a word search puzzle from a list of words. Each puzzle is made with
    a seed, which the link to it holds, so that the link makes it again."""
    q = request.GET
    form = {
        "words": q.get("words", ""),
        "rows": q.get("rows", "12"),
        "cols": q.get("cols", "12"),
        "mask": q.get("mask", ""),
        "difficulty": q.get("difficulty", "medium"),
    }
    context = {
        "form": form,
        "masks": MASK_CHOICES,
        "difficulties": DIFFICULTY_CHOICES,
        "max_size": setting("MAX_SIZE"),
        "max_words": setting("MAX_WORDS"),
        "max_chars": setting("MAX_CHARS"),
    }
    words = words_in(form["words"])
    if not words:
        return render(request, "wordsearch/maker.html", context)
    context["message"] = maker_problem(form, words)
    try:
        seed = int(q["seed"]) if "seed" in q else secrets.randbelow(10**6)
    except ValueError:
        context["message"] = "The seed must be a whole number"
    if context["message"]:
        return render(request, "wordsearch/maker.html", context, status=400)
    if rate_limited(request):
        context["message"] = (
            "Too many puzzles from this address. Please try again later"
        )
        return render(request, "wordsearch/maker.html", context, status=429)
    try:
        grid, placed = puzzle.make_wordsearch(
            words,
            form["nrows"],
            form["ncols"],
            form["mask"] or None,
            form["difficulty"],
            seed=seed,
            time_limit=setting("TIME_LIMIT"),
        )
    except ValueError:
        context["message"] = (
            "The words could not be fitted into the grid. Try a larger grid,"
            " fewer words or another shape"
        )
        return render(request, "wordsearch/maker.html", context)
    params = {key: form[key] for key in ("words", "rows", "cols", "mask", "difficulty")}
    rings = [(i, j, di, dj, len(word)) for word, i, j, di, dj in placed]
    size = f"{form['nrows']} rows and {form['ncols']} columns"
    words = sorted(word.upper() for word in words)
    context.update(
        words=words,
        puzzle_svg=puzzle.grid_svg(grid, label=f"A word search puzzle of {size}"),
        solution_svg=puzzle.grid_svg(
            grid, rings, label="The solution of the puzzle, with each word ringed"
        ),
        puzzle_download=svg_data_uri(puzzle.grid_svg(grid, words=words)),
        solution_download=svg_data_uri(puzzle.grid_svg(grid, rings)),
        permalink="?" + urlencode({**params, "seed": seed}),
        another="?" + urlencode(params),
    )
    return render(request, "wordsearch/maker.html", context)


def solver_problem(grid_text, words_text, grid, words):
    """What is wrong with the solver's form, or None."""
    max_chars, max_size = setting("SOLVER_MAX_CHARS"), setting("SOLVER_MAX_SIZE")
    if len(grid_text) > max_chars or len(words_text) > max_chars:
        return f"The grid and the words may each have at most {max_chars} characters"
    if not grid:
        return "Please enter the grid, one row on each line"
    if len(grid) > max_size or len(grid[0]) > max_size:
        return f"The grid may have at most {max_size} rows and columns"
    if not words:
        return "Please enter the words to find, one on each line"
    if len(words) > setting("SOLVER_MAX_WORDS"):
        return f"Please give at most {setting('SOLVER_MAX_WORDS')} words"
    return None


def solver(request):
    """Find the words in a word search puzzle (a POST form, since a grid can be
    too long for an address)."""
    grid_text = request.POST.get("grid", "")
    words_text = request.POST.get("words", "")
    context = {
        "grid_text": grid_text,
        "words_text": words_text,
        "max_size": setting("SOLVER_MAX_SIZE"),
        "max_words": setting("SOLVER_MAX_WORDS"),
    }
    if request.method != "POST":
        return render(request, "wordsearch/solver.html", context)
    # The grid is parsed only if its text is within the limit.
    too_long = len(grid_text) > setting("SOLVER_MAX_CHARS")
    grid = [] if too_long else puzzle.parse_grid(grid_text)
    words = words_in(words_text)
    context["message"] = solver_problem(grid_text, words_text, grid, words)
    if context["message"]:
        return render(request, "wordsearch/solver.html", context, status=400)
    found = puzzle.find_words(grid, words)
    rings = [
        (i, j, di, dj, len(puzzle.letters_only(word)))
        for word, occurrences in found.items()
        for i, j, di, dj in occurrences
    ]
    results = [
        {
            "word": word.upper(),
            "occurrences": [
                {
                    "row": i + 1,
                    "col": j + 1,
                    "direction": puzzle.DIRECTION_NAMES[di, dj],
                }
                for i, j, di, dj in occurrences
            ],
        }
        for word, occurrences in found.items()
    ]
    context.update(
        results=results,
        nfound=sum(1 for result in results if result["occurrences"]),
        solution_svg=puzzle.grid_svg(
            grid, rings, label="The grid, with each word found ringed"
        ),
    )
    return render(request, "wordsearch/solver.html", context)
