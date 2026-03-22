# Gomoku AI - zapoctovy program

## Specifikace
Program implementuje deskovou hru Gomoku s UI v knihovne Textual.
Podporuje rezimy Human vs AI a AI vs AI. AI pouziva minimax s alpha-beta
prorezavanim, iterativni prohlubovani a heuristicke hodnoceni pomoci patternu.

`gomoku/engine.py` zustava nezmeneny jako herni AI jadro.

## Instalace a spusteni
1. Vytvorte a aktivujte virtualni prostredi.
2. Nainstalujte zavislosti:

`pip3 install .`

3. Spustte hru:

`python -m gomoku`

## Argumenty
- `-s`, `--size` velikost desky (vychozi 15)
- `-w`, `--win` delka vyherni rady (vychozi 5)
- `-t`, `--time` cas na tah AI v sekundach (vychozi 10)
- `-f`, `--fixed` fixni hloubka misto casoveho limitu
- `-m`, `--ai` rezim AI vs AI
- `--swap` kdo provadi Swap-2 setup (`0` random, `1` hrac, `2` AI)

## Ovladani (Textual)
- Klik mysi na pole = polozeni kamene
- Sipky nebo WASD = pohyb kurzoru
- Enter / Space = polozeni na kurzor
- `1` / `2` / `3` = kontextova volba ve Swap-2
- `P` = pauza/pokracovani AI vs AI
- `R` = restart hry
- `Q` = konec aplikace

## Browser mode (online)
Program umi bezet i v prohlizeci pres `textual-serve`:

`python -m gomoku --serve --host 0.0.0.0 --port 8000`

Pak otevri:

`http://<vps-ip>:8000`

Poznamka: AI bezi server-side. Pri vice soucasnych uzivatelich roste CPU zatizeni.

## Dokumentace
- [Uzivatelska dokumentace](docs/user.md)
- [Programatorska dokumentace](docs/programmer.md)
