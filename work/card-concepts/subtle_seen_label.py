from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/tenant/decision_tools/presentation/widgets/property_memory_badge.dart'
s=p.read_text().replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'package:sokoun_app/shared_widgets/sokoun_palette.dart';")
s=s.replace('''          Chip(
            avatar: const Icon(Icons.history, size: 16),
            label: Text(LocaleKeys.personalSeen),
          ),''','''          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.history, size: 14, color: SokounPalette.of(context).muted),
              const SizedBox(width: 4),
              Flexible(
                child: Text(
                  LocaleKeys.personalSeen,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SokounPalette.of(context).muted,
                    fontSize: 11,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ),
            ],
          ),''')
p.write_text(s)
p=root/'test/property_memory_badge_spacing_test.dart'
s=p.read_text().replace("import 'package:flutter_test/flutter_test.dart';", "import 'package:flutter_test/flutter_test.dart';\nimport 'package:melos_core/config/language/locale_keys.g.dart';")
s=s.replace('final chip = tester.getRect(find.byType(Chip));', '''expect(find.byType(Chip), findsNothing);
      expect(find.byIcon(Icons.history), findsOneWidget);
      final chip = tester.getRect(find.text(LocaleKeys.personalSeen));''')
p.write_text(s)
