from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/property_decision_tools.dart')
s=p.read_text()
old='''          widget.selection?.canIdentify == true)
        HousingBudgetEntry('''
new='''          widget.selection?.canIdentify == true) ...[
        const SizedBox(height: 12),
        HousingBudgetEntry('''
assert old in s
s=s.replace(old,new,1)
old='''        ),
      const SizedBox(height: 12),
      FutureBuilder<void>('''
assert old in s
s=s.replace(old,'''        ),
      ],
      const SizedBox(height: 12),
      FutureBuilder<void>(''',1)
p.write_text(s)
