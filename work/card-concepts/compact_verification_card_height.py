from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_verification_tile.dart')
s=p.read_text().replace('child: Column(\n                  crossAxisAlignment:', 'child: Column(\n                  mainAxisSize: MainAxisSize.min,\n                  crossAxisAlignment:')
p.write_text(s)
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/profile_verification_card_layout_test.dart')
s=p.read_text().replace('expect(tile.height, greaterThanOrEqualTo(48));', 'expect(tile.height, greaterThanOrEqualTo(48));\n              if (scale == 1) expect(tile.height, lessThan(150));')
p.write_text(s)
