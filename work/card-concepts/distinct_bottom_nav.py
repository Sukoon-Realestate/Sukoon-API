from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/main_view/presentation/widgets/home_bottom_navigation.dart'
s=p.read_text().replace('color: palette.surface,','color: palette.hero,',1).replace('borderRadius: BorderRadius.circular(24),\n          side: BorderSide(color: palette.line),','borderRadius: BorderRadius.circular(22),',1)
p.write_text(s)
p=root/'lib/features/main_view/presentation/widgets/home_navigation_icon.dart'
s=p.read_text().replace('    required this.size,','    required this.size,\n    this.foregroundColor,',1).replace('  final double size;','  final double size;\n  final Color? foregroundColor;',1).replace('final Color color = isSelected ? palette.text : palette.muted;', 'final Color color = foregroundColor ?? (isSelected ? palette.text : palette.muted);')
p.write_text(s)
p=root/'lib/features/main_view/presentation/widgets/home_navigation_item.dart'
s=p.read_text()
s=s.replace('foregroundColor: palette.accent,','foregroundColor: rail ? palette.accent : palette.onHero,')
s=s.replace('child: Column(\n              mainAxisSize:', '''child: AnimatedContainer(
              duration: SokounMotion.duration(context, milliseconds: 180),
              curve: SokounMotion.curve,
              width: rail ? null : double.infinity,
              padding: rail ? EdgeInsets.zero : const EdgeInsets.symmetric(horizontal: 2, vertical: 8),
              decoration: BoxDecoration(
                color: !rail && selected ? palette.onHero : Colors.transparent,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
              mainAxisSize:''',1)
s=s.replace('color: selected ? palette.chip : Colors.transparent,','color: rail && selected ? palette.chip : Colors.transparent,',1)
s=s.replace('size: rail ? 24.r : 24,','size: rail ? 24.r : 22,\n                    foregroundColor: rail ? null : selected ? palette.hero : palette.heroMuted,',1)
s=s.replace('color: selected ? palette.text : palette.muted,','color: rail ? (selected ? palette.text : palette.muted) : (selected ? palette.hero : palette.heroMuted),',1)
s=s.replace('''              ],
            ),
          ),''','''              ],
              ),
            ),
          ),''',1)
p.write_text(s)
