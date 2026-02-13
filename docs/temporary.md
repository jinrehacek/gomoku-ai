## struktura python kodu
- soubor na IO a interakci s uzivatelem
- soubor engine.py ?? pro samotny engine, ten import do IO? a IO import do main? <- zjistit jak na packaeges v pythonu
  - anebo mozna ne , nemusi to byt package, zejo...
  - ^^^ rozmyslet si
- pyproject.toml a naucit se s tim pracovat
- specifiokvat linter (Ruff), testing framework - nejspis pytest



## IO
- ASCII znaky nebo **TUI (Rich apod.)** (spise TUI pro krasu)
uzivatel zada souradnice , takze hezky vykreslit souradnice a mozna overlay (voditka) ci rovnou moznost kliknout
- ^^^ hodne navic, nejprve standartni at to nejak funguje
- dat do IO moznost loadout cuztom patterns z .csv souboru a uchvat je po dobu hry v nejake var

## engine
minimax + alpha/beta
+ upravy a vylepseni 

## OPENING
hardcoded strategie pro swap 2 a jinak nechat jet engine, pro vybrani strany, heuristicky nikdy nedame druhy swap


## testing
nainstaloat a pouzit nejaky package pak na zjisteni test coverage


## Board
- mozna drzet v pameti, ktery kamen byl polozen posledni? - kvuli check_win a undo_move
- 

## Heuristicka funkce
- kazdou "line" (diagonalu, row, col) projedeem prave jednou "posuvnym oknem" s tim ze pokud mame pattern mensi nez velikost "okna" tak prohledame jeste v tom okne coz je vzdycky tak jako obecne vsechno kde je restrikce na 15x15 O(1) takze je to chill. 
- vzdycky hledam naejdou pro bileho i cerneho - vymyslet elegantni switch for the feeling of superiority
- COZ znamena... musim vyelpsit nebo oddelit a predelat get_daignoals protoze pri win_check neni nutne prohaczet vsechny, tady to ale nutne je 
- budu hledat pro kazdou line? nebo rovnou v loopu pro celou board? rozhodne pro LINE kvuli testabillity => soucet pak passnu jako output fn a pro cely board akorat suma
je bily = -1 * cerny? I guess so...
