from pathlib import Path
base=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/main_view/presentation/widgets')
p=base/'home_bottom_navigation.dart'
s=p.read_text().replace('minimum: const EdgeInsets.fromLTRB(12, 8, 12, 8),', 'minimum: const EdgeInsets.fromLTRB(8, 4, 8, 4),')
s=s.replace('BorderRadius.circular(22)', 'BorderRadius.circular(16)')
s=s.replace('BoxConstraints(minHeight: 76)', 'BoxConstraints(minHeight: 64)')
s=s.replace('EdgeInsets.symmetric(horizontal: 4.w, vertical: 8)', 'EdgeInsets.symmetric(horizontal: 4.w, vertical: 4)')
p.write_text(s)
p=base/'home_navigation_item.dart'
s=p.read_text().replace('const EdgeInsets.symmetric(horizontal: 2, vertical: 8)', 'const EdgeInsets.symmetric(horizontal: 2, vertical: 4)')
p.write_text(s)
