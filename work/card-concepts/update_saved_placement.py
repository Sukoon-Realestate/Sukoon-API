from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/docs/ui-refactor/REFERENCE-ADAPTATION.md')
s=p.read_text().replace("| Saved searches and decision tools | Home Tools and Saved's More menu |", "| Saved searches and decision tools | Bookmark icon in the individual Home header (tooltip and accessibility label retained), plus Home Tools and Saved's More menu. The former full-width Home text row is removed; the Home guide's Saved target follows the header icon. |")
p.write_text(s)
