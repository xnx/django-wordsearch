# Changelog

## 0.2.0 (25 November 2026)

- The maker keeps a share of the words diagonal in a crowded grid, in which, before, most or all of them could read along rows and columns, where words pack most easily. At medium and hard, the diagonal directions are tried first while fewer than half of the words read diagonally, and the places where a word shares the most letters with words already written are tried first, which packs the words more tightly. For 22 words (128 letters) in a 12×12 grid, at medium, 47% of the words read diagonally on average over 20 seeds, and at least 36% in each puzzle, against 39% and 5% before. An 11×11 grid, which was filled for 7 of the 20 seeds, is now filled for all of them, though still with few diagonal words (13% on average).
- In a grid too crowded for diagonal words, the share of them aimed for falls to nothing over the first 100 searches, so that such a grid is still filled.
- A word is never written wholly over letters already in the grid, such as EAR along EARTH, where it would be found only within other words.
- A seed makes a different puzzle from the one that it made in 0.1.0, so that a link to a puzzle made with 0.1.0 makes a new puzzle.

## 0.1.0 (24 November 2026)

The first release, from the app that runs at https://scipython.com/apps/wordsearch/.

- A maker: words hidden in a rectangular or shaped (circle or squares) grid at three difficulties, by a depth-first search with restarts and a time limit, with the other cells filled with letters drawn from the words.
- A link to each puzzle, which holds its seed and makes it again; the puzzle and its solution, with each word ringed, as SVG images; a printed page of just the puzzle and its words.
- A solver: every occurrence of each word, in all eight directions, ringed on the grid and listed by row, column and direction.
- An optional rate limit on the maker, by the visitor's address, with a hook for sites behind a proxy.
- Templates and a stylesheet with no dependence on a CSS framework, in the page's colours and font unless a site sets its own.
- `wordsearch.puzzle`, which makes, solves and draws puzzles with only Python's standard library.
