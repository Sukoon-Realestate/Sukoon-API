from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/main_view/presentation/widgets')
p=root/'home_bottom_navigation.dart'
s=p.read_text().replace('color: palette.hero,','color: palette.surface,',1)
p.write_text(s)
p=root/'home_navigation_item.dart'
s=p.read_text().replace('foregroundColor: rail ? palette.accent : palette.onHero,','foregroundColor: rail ? palette.accent : palette.text,')
s=s.replace('!rail && selected ? palette.onHero : Colors.transparent','!rail && selected ? palette.raised : Colors.transparent')
s=s.replace('palette.heroMuted','palette.muted').replace('palette.hero','palette.text')
p.write_text(s)
