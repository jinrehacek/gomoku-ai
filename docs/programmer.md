# Programatorska dokumentace

## Hlavni struktura programu
Veskery kod je ve slozce `gomoku`. Projekt je rozdelen na logickou vrstvu
(`board.py`, `engine.py`) a UI vrstvu (`tui.py`, `__main__.py`).

### Board & `board.py`
`Board` reprezentuje herni desku, uklada historii tahu a umi zjistit konec hry.

### Engine & `engine.py`
`engine.py` obsahuje minimax, alpha-beta, iterativni prohlubovani a evaluaci.
V ramci migrace na Textual nebyl menen.

### IO helpery & `io.py`
`io.py` uz neni terminalova Rich vrstva. Obsahuje pouze:
- validaci vstupniho formatu souradnic (`valid_input`)
- prevod textoveho formatu na interni `(x, y)` (`board_coords_to_xy`)
- prevod `(x, y)` na text (`xy_to_board_coords`)

### Textual UI & `tui.py`
`tui.py` obsahuje:
- `BoardView`: vykresleni desky, kurzoru, posledniho tahu, click handling
- `GomokuApp`: herni stavy, swap-2 flow, rezimy hry, klavesove vazby,
  asynchronni AI tahy ve vlakne

UI je stavovy stroj podle `phase`:
- `human_swap_3`
- `ai_swap_choice`
- `ai_swap_add2`
- `play`
- `game_over`

AI vypocet se spousti mimo UI thread, aby aplikace zustala responsivni.

### Entry point & `__main__.py`
`__main__.py`:
- parsuje argumenty
- validuje jejich hodnoty
- spousti lokalni Textual aplikaci
- nebo spousti browser mode (`--serve`) pres `textual-serve`

V `--serve` modu se startuje HTTP server, ktery vytvori samostatny Textual proces
pro browser klienta.

## Testovani
Pouzity framework je `pytest`.

Aktualni testy pokryvaji:
- `board.py`
- `engine.py`
- helper funkce v `io.py`

Po migraci byly odstraneny testy zavisle na Rich table renderingu a nahrazeny
testem `xy_to_board_coords`.

Spusteni:

`pytest`

Kontrola stylu:

`ruff check`
