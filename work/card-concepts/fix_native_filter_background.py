from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/shared_widgets/sokoun_theme.dart'
s=p.read_text().replace('chipTheme: ChipThemeData(\n        backgroundColor: Colors.transparent,','chipTheme: ChipThemeData(\n        // RawChip paints on a canvas Material; match the page to avoid a white pill.\n        backgroundColor: tokens.canvas,').replace('        disabledColor: Colors.transparent,','        disabledColor: tokens.canvas,')
p.write_text(s)
p=root/'test/reference_filter_style_test.dart'
s=p.read_text().replace('expect(Theme.of(context).chipTheme.backgroundColor!.a, 0);','expect(Theme.of(context).chipTheme.backgroundColor, palette.canvas);')
p.write_text(s)
