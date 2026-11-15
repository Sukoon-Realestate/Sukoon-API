from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/visit_decisions/presentation/screens/visit_agenda_screen.dart')
s=p.read_text()
old='''            TabBar(
              isScrollable: true,
'''
new='''            TabBar(
              isScrollable: true,
              tabAlignment: TabAlignment.start,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              labelPadding: const EdgeInsets.symmetric(horizontal: 12),
'''
assert s.count(old)==1
p.write_text(s.replace(old,new))
