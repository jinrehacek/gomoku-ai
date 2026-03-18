# Uživatelská dokumentace

## Spuštění
Program se spouští příkazem:

`python gomoku`

Volitelné argumenty:
- `-s`, `--size` velikost desky (výchozí 15)
- `-w`, `--win` délka výherní řady (výchozí 5)
- `-t`, `--time` čas na tah AI v sekundách (výchozí 10)
- `-f`, `--fixed` fixní hloubka minimaxu (pokud je > 0, ignoruje čas)
- `-m`, `--ai` režim AI vs AI
- `--swap` kdo provádí Swap-2 setup (`1` hráč, `2` AI)


## Ovládání
- Souřadnice se zadávají ve formátu `písmeno+číslo`, např. `a1`, `g8`, `h12`.
- Písmeno určuje sloupec, číslo určuje řádek.
- Po každém tahu se deska znovu vykreslí v terminálu.


## Režimy hry
- **Člověk vs AI**
  - hraje člověk proti počítači
  - při spuštění bez `-m` se režim volí interaktivně
- **AI vs AI**
  - obě strany hraje AI
  - spouští se přepínačem `-m`

## Swap-2
V programu se hraje Gomoku podle turnajových pravidel, která eliminují jistou výhru začínajícího hráče. Začít Swap2 může buď hráč nebo počítač. Nutno upozornit, že není implementována možnost, kde počítač položí další dva kameny. Více o Swap2 se dočtete [zde](https://cs.wikipedia.org/wiki/SWAP).

## Příklady spuštění
- Základní hra:
  - `python gomoku`
- AI vs AI:
  - `python gomoku --ai`
- Větší deska a delší čas:
  - `python gomoku -size 19 --time 20`
- Fixní hloubka místo času:
  - `python gomoku --fixed 3`
