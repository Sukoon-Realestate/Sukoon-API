from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/docs/ui-refactor/REFERENCE-ADAPTATION.md')
s=p.read_text()+'''\n\n## Conversations header — 2026-11-15\n\n| Capability | Revised placement and outcome |\n| --- | --- |\n| Conversations title, notification bell, reply reminders and media/storage settings | Combined in the chat page toolbar rather than a bell-only workspace row above a second title/actions row. Existing notification roles/counts and destinations remain; shell read/runtime notices remain. Company account settings retain their toolbar entry. |\n'''
p.write_text(s)
