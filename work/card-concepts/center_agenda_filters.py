from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/visit_decisions/presentation/screens/visit_agenda_screen.dart')
s=p.read_text().replace('tabAlignment: TabAlignment.start,', 'tabAlignment: TabAlignment.center,')
p.write_text(s)
