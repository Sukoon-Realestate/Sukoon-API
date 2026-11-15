from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/docs/ui-refactor/REFERENCE-ADAPTATION.md')
s=p.read_text().replace('dock with an animated tonal icon highlight and persistent text labels.', 'pine dock with an animated light full-tab selection tile and persistent text labels. Explicit hero/onHero colors keep inactive content readable.')
p.write_text(s)
