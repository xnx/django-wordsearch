# Changelog

## 0.1.0 (unreleased)

The first release, from the app that runs at https://scipython.com/apps/wordsearch/.

- A maker: words hidden in a rectangular or shaped (circle or squares) grid at three difficulties, by a depth-first search with restarts and a time limit, with the other cells filled with letters drawn from the words.
- A link to each puzzle, which holds its seed and makes it again; the puzzle and its solution, with each word ringed, as SVG images; a printed page of just the puzzle and its words.
- A solver: every occurrence of each word, in all eight directions, ringed on the grid and listed by row, column and direction.
- An optional rate limit on the maker, by the visitor's address, with a hook for sites behind a proxy.
- Templates and a stylesheet with no dependence on a CSS framework, in the page's colours and font unless a site sets its own.
- `wordsearch.puzzle`, which makes, solves and draws puzzles with only Python's standard library.
