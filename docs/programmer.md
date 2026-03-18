# Programátorská dokumentace

## Hlavní struktura programu
Veškerý kód samotného programu je umístěn ve složce `gomoku`; díky existenci `__init__.py` se `gomoku` chová také jako package.
Ve složce je kód dekomponován do 4 souborů: `board.py`, `engine.py`, `io.py` a `__main__.py`.


### Board & board.py
V souboru `board.py` je kromě několika konstant, které jsou rozumné základní hodnoty, hlavně třída `Board`. Třída `Board` je reprezentací herní desky s velkým množstvím metod, pamatuje si také pořadí tahů a je schopna určit, zda a jak hra skončila.


#### Významné metody:
- Board.place(x, y) -> void:
  - vloží kámen/symbol na zadané souřadnice, pokud je to možné, jinak vědomě vyvolá chybu
  - nutno zmínit, že **X** je řádek, **Y** je sloupec (není to intuitivní)
- Board.undo_move(x, y) -> void:
  - vrátí poslední tah podle interního seznamu `board.history`
- Board.is_over() -> int:
  - pakliže byl nějaký tah zahrán jako poslední, zkontroluje části herní plochy, na kterých po tomto tahu mohlo dojít k výhře, případně k naplnění celé plochy (tedy remíze)
  - pokud je `self.history` prázdný, pak zkontroluje celou plochu na výherní sekvence
- _get_all_lines, _get_xy_diag/row/col/ atd.
  - pomocné metody, které vrátí pouze řádek/sloupec obsahující dané souřadnice


#### Uložená data:
- self.history - seznam tahů
- board.turn - kontroluje a drží, jaký hráč má nyní táhnout
- board.size - velikost herní plochy
- board.win_len - kolik kamenů/symbolů za sebou vyhrává

### Engine & engine.py
Soubor `engine.py` obsahuje hlavní logiku a algoritmus projektu. Je zde Alpha-Beta Minimax a mnoho funkcí, které jsou pomocné pro samotný minimax algoritmus nebo jej obalují (např. postupné prohlubování vyhledávání). Skoro všechny funkce obsahují `Board` jako parametr.

#### Významné třídy:
- `SearchState`
  - pomocná třída, jejíž objekt - *stav* - předáváme jak v průběhu samotného minimax průchodu, tak i v průběhu postupného prohlubování
  - pamatuje si, které tahy způsobily velké ořezání alpha-beta intervalu, proto je zkusíme prohledat následně dříve -> zrychlení prohledávání
  - pamatuje si (v celém běhu jednoho hledání tahu) počítadlo, kolik stavů jsme prošli, z důvodu kontroly, jestli už nepřetahujeme čas
- `WeAreSlow`
  - speciální Exception, kterou používáme pro ukončení prohledávání i v průběhu jednoho běhu minimaxu


#### Přehled funkcí:
- Generování možných tahů: `get_candidate_moves`, `_candidate_distance`
  - generujeme všechny možné tahy ve dané vzdálenosti od již položených kamenů; na začátku generujeme pouze do vzdálenosti 1, později 2 (šetříme tak v počáteční fázi čas)
  - tahy jsou seřazeny v Čebyševově vzdálenosti od posledního tahu
- Taktické řazení tahů: `_move_wins_for`, `_order_moves_tactical`
  - každý tah zkoušíme nejdříve takticky; pokud existuje takový, co okamžitě na místě vyhraje, pak není nutné do minimaxu posílat "nudné" tahy
  - také kontrolujeme, jestli není nějaká souřadnice, kde by oponent mohl rovnou vyhrát; pokud máme blokující tahy, pak opět nepotřebujeme "nudné" tahy
  - jinak nudné tahy seřadíme podle toho, jak velký cutoff historicky způsobily
- Heuristika a vzorce: `black_stones_eq`, `prepare_patterns`, `eval_line`, `eval_move`, `eval_board`
  - máme hardcoded konstantu se vzorci a jejich taktickými hodnotami
  - při prohledávání herního stromu si předáváme celkovou evaluaci plochy a vždy ji měníme jen podle tahu, který zrovna zkoušíme (velmi to šetří čas)
  - máme pomocné funkce, které rozšíří vzorce o zrcadlové kopie, pakliže nejde o palindromy, a o vzorce z pohledu druhé strany
- Vyhledávání: `check_time`, `minimax`, `get_best_move`, `iterative_deepening`
  - iterativní prohlubování nejdříve prohledává do hloubky 1, poté do hloubky 2 atd.
  - když dojde zadaný čas (kontrolujeme průběžně), vrátí nejlepší tah z poslední dokončené hloubky


### IO & io.py
Soubor `io.py` řeší vykreslování desky v terminálu (Rich), validaci vstupu a herní tok mezi hráčem a AI.


#### Přehled funkcí:
- Vykreslování: `create_table`, `redraw_board`
  - `create_table` vytvoří Rich tabulku s osami, symboly a zvýrazněním posledního tahu
  - `redraw_board` smaže terminál a vytiskne aktuální stav desky
- Validace vstupu a převod souřadnic: `board_coords_to_xy`, `get_inp_num`
  - `board_coords_to_xy` převádí textové souřadnice na interní `(x, y)` a zároveň kontroluje hranice i obsazenost pole 
- Volba režimu hry: `pick_mode_and_swap`
  - řeší výběr mezi Human vs AI a AI vs AI a zároveň určí, kdo provede Swap-2 setup
- Swap-2 logika: `computer_chooses_side`, `human_swap`, `ai_swap`, `ai_vs_ai_swap`
  - obsahuje kompletní průběh otevíracího pravidla Swap-2 pro všechny režimy
  - po setupu pozice rozhoduje, která strana bude hrát člověk/AI a případně provede navazující tah
- Tahy hráče a AI: `human_move`, `ai_move`
  - `human_move` načte, validuje tah hráče a po zahrání překreslí desku
  - `ai_move` vybere tah pomocí engine (`iterative_deepening` nebo `get_best_move` s fixni hloubkou), zahraje ho a vypíše základní statistiku


### Herni logika & __main__.py
Soubor `__main__.py` je vstupní bod aplikace (`python -m gomoku`) a drží hlavní herní smyčky.


#### Přehled:
- Parsování argumentů (`argparse`)
  - nastavuje parametry hry (`size`, `win`, `time`, `fixed`, `ai`, `swap`) a kontroluje, že dávají smysl
- `play_human_vs_ai`
  - hlavní smyčka pro režim člověk proti AI; střídá tahy podle `board.turn` a po každém tahu kontroluje konec hry
- `play_ai_vs_ai`
  - hlavní smyčka pro režim AI proti AI; po úvodním Swap-2 setupu nechá obě AI hrát až do konce
- `main`
  - vytvoří desku, zvolí režim, provede Swap-2 fázi a spustí odpovídající herní smyčku



