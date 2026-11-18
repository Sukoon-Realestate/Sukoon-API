from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/docs/ui-refactor/REFERENCE-ADAPTATION.md')
s=p.read_text()
s+='''

## Bottom navigation redesign · 2026-11-15

The existing role-specific destinations keep their order, labels, routes, access
checks and restored tab state. The mobile bar now uses an inset opaque rounded
dock with an animated tonal icon highlight and persistent text labels. Unread
counts remain inside the icon slot and cap visually at 99+ while semantics retain
the full count. Selected-tab taps now reach the existing reselection handler.
Keyboard hiding, bottom safe-area clearance and large-text scrolling remain owned
by the existing shell. Desktop rail destinations share the icon/selection fixes.
'''
p.write_text(s)
