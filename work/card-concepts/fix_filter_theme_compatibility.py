from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/shared_widgets/sokoun_theme.dart')
s=p.read_text().replace('AppTextStyles.medium14,', 'AppTextStyles.medium,\n          size: 14,')
s=s.replace('        materialTapTargetSize: MaterialTapTargetSize.padded,\n','')
p.write_text(s)
