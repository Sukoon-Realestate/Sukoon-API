# Housing budget sheet cleanup

Reduced the introduction typography, added breathing room around the advertised rent/deposit summary, and made its explanatory copy smaller. Estimates now use one category heading followed by a dense amount field and frequency control with a 12px gap; categories have 20px separation and no additional outer card borders. Deposit separation, unknown-price/cost explanations, estimate disclaimer, split simulation, changed-source warning, save failures and calculation results remain visible in their original flow.

No calculation or persistence changes. Blank amounts remain unknown, exact minor-unit parsing and per-category frequencies remain intact, and save/loading behavior is retained.

32 checks passed: 16 budget layout/input/save combinations covering Arabic/English, light/dark, 320/390 widths and 1x/2x text, plus existing decision and experience calculation checks. Input-to-frequency separation checked; entering 500 saves 50000 minor units and untouched values stay unknown. Arabic preview inspected. Formatting and diff whitespace checks passed. Live device/keyboard review was not performed.
