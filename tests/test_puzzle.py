import pytest

from wordsearch import puzzle

PLANETS = [
    "Mercury",
    "Venus",
    "Earth",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
]


def test_every_word_is_hidden_where_it_says():
    for difficulty, directions in puzzle.DIRECTIONS.items():
        grid, placed = puzzle.make_wordsearch(
            PLANETS, 7, 7, difficulty=difficulty, seed=1
        )
        assert sorted(word for word, *_ in placed) == sorted(w.upper() for w in PLANETS)
        for word, i, j, di, dj in placed:
            assert puzzle.reads(grid, word, i, j, di, dj)
            assert (di, dj) in directions
        assert all(letter.isalpha() for row in grid for letter in row)


def test_a_seed_always_makes_the_same_puzzle():
    assert puzzle.make_wordsearch(PLANETS, 7, 7, seed=5) == puzzle.make_wordsearch(
        PLANETS, 7, 7, seed=5
    )


def test_the_filler_is_drawn_from_the_letters_of_the_words():
    grid, _ = puzzle.make_wordsearch(["ABAB", "BABA"], 6, 6, seed=3)
    assert {letter for row in grid for letter in row} == {"A", "B"}


def test_masks_leave_cells_blank_symmetrically():
    for mask in puzzle.MASKS:
        for n in (10, 11):
            grid, placed = puzzle.make_wordsearch(
                ["New York", "Ohio", "Texas"], n, n, mask=mask, seed=2
            )
            blank = [[letter == puzzle.MASKED for letter in row] for row in grid]
            assert any(map(any, blank))
            assert blank == blank[::-1] == [row[::-1] for row in blank]
            assert "NEWYORK" in [word for word, *_ in placed]


def test_words_that_do_not_fit_raise_an_error():
    with pytest.raises(ValueError):
        puzzle.make_wordsearch(
            ["ABC", "DEF", "GHI", "JKL"], 3, 3, difficulty="easy", time_limit=0.2
        )


def test_grids_are_read_with_or_without_spaces():
    assert puzzle.parse_grid("\nS N M\nA E E\n") == [list("SNM"), list("AEE")]
    assert puzzle.parse_grid("snm\nae.\nx") == [
        list("SNM"),
        ["A", "E", "*"],
        ["X", "*", "*"],
    ]
    # make_wordsearch.py prints a shaped grid with a space for a blank cell.
    assert puzzle.parse_grid("  O H\nA B C D") == [
        ["*", "O", "H", "*"],
        list("ABCD"),
    ]
    assert puzzle.parse_grid("\n \n") == []


def test_words_are_found_in_every_direction():
    grid = puzzle.parse_grid("CAT\nXOX\nTAC")
    found = puzzle.find_words(grid, ["cat", "TOT", "A-O-A", "dog"])
    assert found["cat"] == [(0, 0, 0, 1), (2, 2, 0, -1)]
    # A palindrome reads the same both ways, but is found once.
    assert len(found["TOT"]) == 1 and len(found["A-O-A"]) == 1
    assert found["dog"] == []


def test_the_svg_has_a_ring_for_each_word_and_escapes_its_text():
    grid = puzzle.parse_grid("CAT\nXOX\nTAC")
    svg = puzzle.grid_svg(grid, [(0, 0, 0, 1, 3)], words=["<cat>"], label='"A" & B')
    assert svg.count("<rect ") == 2  # the background and one ring
    assert "&lt;CAT&gt;" in svg and "<cat>" not in svg
    assert 'aria-label="&quot;A&quot; &amp; B"' in svg
    assert 'class="ws-letters" fill="black"' in svg
