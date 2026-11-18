from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/main_view/presentation/widgets/home_navigation_item.dart')
s=p.read_text().replace('color: !rail && selected ? palette.raised : Colors.transparent,','color: Colors.transparent,')
p.write_text(s)
