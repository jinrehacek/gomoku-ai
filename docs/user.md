# Uzivatelska dokumentace

## Spusteni
Program se spousti prikazem:

`python -m gomoku`

Volitelne argumenty:
- `-s`, `--size` velikost desky (vychozi 15)
- `-w`, `--win` delka vyherni rady (vychozi 5)
- `-t`, `--time` cas na tah AI v sekundach (vychozi 10)
- `-f`, `--fixed` fixni hloubka minimaxu (pokud je > 0, ignoruje cas)
- `-m`, `--ai` rezim AI vs AI
- `--swap` kdo provadi Swap-2 setup (`0` random, `1` hrac, `2` AI)

## Ovladani
- Klik mysi na pole = polozeni kamene
- Sipky nebo WASD = pohyb kurzoru
- Enter / Space = polozeni na kurzor
- `1` / `2` / `3` = volba v kontextu Swap-2 faze
- `P` = pauza nebo pokracovani AI vs AI
- `R` = restart hry
- `Q` = ukonceni aplikace

## Rezimy hry
- **Clovek vs AI**
  - hraje clovek proti pocitaci
  - pri `--swap 0` se zvoli nahodne, kdo nastavuje Swap-2
- **AI vs AI**
  - obe strany hraje AI
  - spousti se prepinacem `-m`
  - lze pozastavit klavesou `P`

## Swap-2
Podporovane jsou oba setup proudy:
- Human setup 3 kameny (X, O, X)
- AI setup + volba strany / pridani 2 kamenu

Poznamka: AI stale nepouziva variantu, kdy AI sama aktivne vybira pridani dalsich 2 kamenu.

## Browser mode
Program lze vystavit do browseru:

`python -m gomoku --serve --host 0.0.0.0 --port 8000`

Potom otevri:

`http://<server-ip>:8000`

## Nasazeni pres Docker a Reverse Proxy (VPS)
Pro nasazeni na VPS s reverse proxy (např. Nginx, Caddy) muzes vyuzit pribaleny `Dockerfile`.
Pokud aplikace bezi za HTTPS domenou, je nutne nastavit spravnou verejnou URL, aby fungovaly websockety:

`docker build -t gomoku .`
`docker run -p 8000:8000 -e PUBLIC_URL="https://tvoje-domena.cz" gomoku`

Nebo pri spusteni Pythonu:
`python -m gomoku --serve --host 0.0.0.0 --port 8000 --url https://tvoje-domena.cz`

## Priklady spusteni
- Zakladni hra:
  - `python -m gomoku`
- AI vs AI:
  - `python -m gomoku --ai`
- Vetsi deska a delsi cas:
  - `python -m gomoku --size 19 --time 20`
- Fixni hloubka misto casu:
  - `python -m gomoku --fixed 3`
- Browser mode:
  - `python -m gomoku --serve --host 0.0.0.0 --port 8000`
