## struktura python kodu
- soubor na IO a interakci s uzivatelem
- soubor engine.py ?? pro samotny engine, ten import do IO? a IO import do main? <- zjistit jak na packaeges v pythonu
  - anebo mozna ne , nemusi to byt package, zejo...
  - ^^^ rozmyslet si
- pyproject.toml a naucit se s tim pracovat
- specifiokvat linter (Ruff), testing framework - nejspis pytest



## IO
ASCII znaky nebo **TUI (Rich apod.)** (spise TUI pro krasu)
uzivatel zada souradnice , takze hezky vykreslit souradnice a mozna overlay (voditka) ci rovnou moznost kliknout
^^^ hodne navic, nejprve standartni at to nejak funguje

## engine
minimax + alpha/beta
+ upravy a vylepseni 

## OPENING
hardcoded strategie pro swap 2 a jinak nechat jet engine, pro vybrani strany, heuristicky nikdy nedame druhy swap


## testing
nainstaloat a pouzit nejaky package pak na zjisteni test coverage
