# Gomoku AI - zápočtový program

## Specifikace
Program implementuje deskovou hru Gomoku v terminálu (TUI přes knihovnu Rich), včetně režimů Human vs AI a AI vs AI. Herní AI používá minimax s alpha-beta prořezáváním, iterativní prohlubování a heuristické hodnocení pozice pomocí patternů.

## Instalace a spuštění
1. Vytvořte a aktivujte virtuální prostředí. (Doporučeno, například pomocí python3-venv)
2. Nainstalujte projekt/dependencies: 

`pip3 install .` jediná dependency je package Rich

3. Spusťte hru:

`python gomoku`

Základní parametry:
- `-s`, `--size` velikost desky (výchozí 15)
- `-w`, `--win` délka výherní řady (výchozí 5)
- `-t`, `--time` čas na tah AI v sekundách (výchozí 10)
- `-f`, `--fixed` fixní hloubka místo časového limitu
- `-m`, `--ai` režim AI vs AI
- `--swap` kdo provádí Swap-2 setup (`1` člověk, `2` AI)

Podrobnější popis ovládání je v uživatelské dokumentaci.

## Dokumentace
- [Uživatelská dokumentace](docs/user.md)
- [Ukázky použití](docs/examples.md)
- [Programátorská dokumentace](docs/programmer.md)
