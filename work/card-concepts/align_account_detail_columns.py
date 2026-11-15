from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_account_detail_row.dart')
s=p.read_text()
s=s.replace('''          ? TextAlign.right
          : TextAlign.left,''','''          ? TextAlign.left
          : TextAlign.right,''')
s=s.replace('''            Expanded(flex: 3, child: valueText),
            Flexible(flex: 2, child: labelText),''','''            Expanded(flex: 2, child: labelText),
            Expanded(flex: 3, child: valueText),''')
p.write_text(s)
