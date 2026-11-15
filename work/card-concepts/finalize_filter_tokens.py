from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib')
p=root/'shared_widgets/sokoun_theme.dart'
s=p.read_text().replace('text(AppTextStyles.medium14, color: chipForeground)', 'text(AppTextStyles.medium, size: 14, color: chipForeground)')
p.write_text(s)
p=root/'features/tenant/home/presentation/widgets/tenant_filter/filter_chip_wrap.dart'
s=p.read_text().replace("import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';\n", '')
p.write_text(s)
