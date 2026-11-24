import itertools
import re

import pytest
from django.core.cache import cache
from django.test import Client

# The puzzles' images, not any icons in a site's pages.
SVG = re.compile(r'<svg [^>]*role="img".*?</svg>', re.DOTALL)


@pytest.fixture(autouse=True)
def _empty_cache():
    cache.clear()


def test_the_default_page_is_a_page_of_its_own():
    html = Client().get("/wordsearch/").content.decode()
    assert html.startswith("<!doctype html>")
    assert "Word Search maker" in html and "wordsearch/wordsearch.css" in html


def test_a_puzzle_is_made_again_by_its_link():
    client = Client()
    query = {
        "words": "Mercury\nVenus, Earth\nMars",
        "rows": "7",
        "cols": "7",
        "difficulty": "hard",
        "seed": "3",
    }
    html = client.get("/wordsearch/", query).content.decode()
    assert "MERCURY" in html and "EARTH" in html and "Download the puzzle" in html
    assert "seed=3" in html
    assert len(SVG.findall(html)) == 2
    again = client.get("/wordsearch/", query).content.decode()
    assert SVG.findall(again) == SVG.findall(html)
    # Without a seed, one is chosen and given in the link to the puzzle.
    del query["seed"]
    assert "seed=" in client.get("/wordsearch/", query).content.decode()


def test_the_maker_validates_its_input():
    client = Client()

    def get(**query):
        query = {"words": "Venus", "rows": "7", "cols": "7", **query}
        return client.get("/wordsearch/", query)

    assert get(rows="40").status_code == 400
    assert b"from 2 to 32 rows" in get(rows="40").content
    assert b"whole numbers" in get(cols="x").content
    assert b"too many letters" in get(words="Mercury", rows="5", cols="5").content
    assert b"fewer than two letters" in get(words="Venus\nI").content
    assert b"shapes listed" in get(mask="star").content
    assert b"difficulties listed" in get(difficulty="fiendish").content
    assert b"seed must be" in get(seed="abc").content
    words = ["".join(pair) for pair in itertools.product("ABCDEFGHIJKLM", repeat=2)]
    assert b"at most 150 words" in get(words="\n".join(words[:151])).content
    html = get(words="<b>bold</b>").content.decode()
    assert "<b>bold" not in html and "&lt;B&gt;BOLD&lt;/B&gt;" in html


def test_the_maker_says_when_the_words_do_not_fit(settings):
    settings.WORDSEARCH_TIME_LIMIT = 0.1
    query = {
        "words": "ABC\nDEF\nGHI\nJKL",
        "rows": "3",
        "cols": "3",
        "difficulty": "easy",
    }
    assert b"could not be fitted" in Client().get("/wordsearch/", query).content


def test_the_maker_is_rate_limited_by_the_visitors_address(settings):
    settings.WORDSEARCH_RATE_LIMIT_PER_HOUR = 1
    settings.WORDSEARCH_CLIENT_IP = "tests.test_views.forwarded_for"
    query = {"words": "Venus\nMars", "rows": "6", "cols": "6"}

    def get(address):
        return Client().get("/wordsearch/", query, HTTP_X_FORWARDED_FOR=address)

    assert get("192.0.2.1").status_code == 200
    assert get("192.0.2.1").status_code == 429
    assert get("192.0.2.2").status_code == 200


def forwarded_for(request):
    return request.META["HTTP_X_FORWARDED_FOR"]


def test_the_solver_finds_words_and_reports_those_missing():
    client = Client()
    assert b"Word Search solver" in client.get("/wordsearch/solve/").content
    html = client.post(
        "/wordsearch/solve/", {"grid": "C A T\nX O X\nT A C", "words": "cat\ndog"}
    ).content.decode()
    assert "<strong>1</strong> of 2 words found" in html
    assert "row 1, column 1, reading right" in html
    assert "row 3, column 3, reading left" in html
    assert "not found" in html
    assert len(SVG.findall(html)) == 1


def test_the_solver_validates_its_input():
    client = Client()
    response = client.post("/wordsearch/solve/", {"grid": "", "words": "cat"})
    assert response.status_code == 400 and b"enter the grid" in response.content
    response = client.post("/wordsearch/solve/", {"grid": "CAT", "words": ""})
    assert b"words to find" in response.content
    big = "\n".join(["A" * 51] * 3)
    response = client.post("/wordsearch/solve/", {"grid": big, "words": "AA"})
    assert b"at most 50 rows" in response.content
    response = client.post("/wordsearch/solve/", {"grid": "A" * 10_001, "words": "AA"})
    assert b"at most 10000 characters" in response.content
