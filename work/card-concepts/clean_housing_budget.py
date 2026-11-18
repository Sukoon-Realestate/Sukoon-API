from pathlib import Path
base=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets')
p=base/'housing_budget_form.dart'
s=p.read_text()
s="import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';\nimport 'package:sokoun_app/shared_widgets/sokoun_settings_section.dart';\n"+s
s=s.replace('style: Theme.of(context).textTheme.titleLarge,', 'style: Theme.of(context).textTheme.titleMedium,')
s=s.replace('''            Text(LocaleKeys.exBudgetHelp),''','''            const SizedBox(height: 6),
            Text(LocaleKeys.exBudgetHelp,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: SokounPalette.of(context).muted, height: 1.5)),
            const SizedBox(height: 16),''')
s=s.replace("PropertyCostCard(cost: widget.cost, periodLabel: ''),", "PropertyCostCard(cost: widget.cost, periodLabel: '', compact: true),\n            const SizedBox(height: 8),")
s=s.replace('''            Text(LocaleKeys.exDepositSeparate),''','''            Text(LocaleKeys.exDepositSeparate,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: SokounPalette.of(context).muted, height: 1.5)),
            const SizedBox(height: 12),''')
s=s.replace('padding: const EdgeInsets.symmetric(vertical: 8),', 'padding: const EdgeInsets.only(bottom: 12),',1)
s=s.replace('''                child: Column(
                  children: [''', '''                child: SokounSettingsSection(
                  title: _label(key),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    spacing: 12,
                    children: [''',1)
s=s.replace("labelText: '${_label(key)} · ${LocaleKeys.exEstimate}',", "labelText: LocaleKeys.exEstimate,\n                        isDense: true,\n                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),")
s=s.replace('''                              labelText: LocaleKeys.exFrequency,
''','''                              labelText: LocaleKeys.exFrequency,
                              isDense: true,
                              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
''',1)
s=s.replace('''                    ),
                  ],
                ),
              ),
            ValueListenableBuilder(''', '''                    ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 8),
            ValueListenableBuilder(''',1)
s=s.replace('''            if (widget.failed) Text(LocaleKeys.freeLocalSaveFailed),''', '''            const SizedBox(height: 16),
            if (widget.failed) Text(LocaleKeys.freeLocalSaveFailed),''')
s=s.replace('''              builder: (_, saved, __) => Column(
                crossAxisAlignment:''','''              builder: (_, saved, __) => Column(
                spacing: 8,
                crossAxisAlignment:''')
p.write_text(s)
p=base/'property_cost_card.dart'
s=p.read_text().replace('    required this.periodLabel,', '    required this.periodLabel,\n    this.compact = false,')
s=s.replace('  final String periodLabel;', '  final String periodLabel;\n  final bool compact;')
s=s.replace('''          height: 1.5,
''','''          height: 1.5,
          style: compact ? Theme.of(context).textTheme.bodySmall : null,
''',1)
p.write_text(s)
