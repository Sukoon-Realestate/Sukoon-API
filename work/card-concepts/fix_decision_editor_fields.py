from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/decision_editor.dart')
s=p.read_text()
s="import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';\n"+s
s=s.replace('''              maxLength: 60,
              decoration: InputDecoration(
                labelText: LocaleKeys.freeDecisionList,
                hintText: LocaleKeys.freeDecisionListExample,
              ),''','''              maxLength: 60,
              useGlass: false,
              decoration: _decoration(context, LocaleKeys.freeDecisionList).copyWith(
                hintText: LocaleKeys.freeDecisionListExample,
              ),''')
s=s.replace('''              maxLines: 4,
              maxLength: 4000,
              decoration: InputDecoration(
                labelText: LocaleKeys.freePrivateNotes,
              ),''','''              minLines: 4,
              maxLines: 6,
              maxLength: 4000,
              useGlass: false,
              decoration: _decoration(context, LocaleKeys.freePrivateNotes).copyWith(
                alignLabelWithHint: true,
              ),''')
pos=s.index('  String? _validateList(')
s=s[:pos]+'''  InputDecoration _decoration(BuildContext context, String label) {
    final palette = SokounPalette.of(context);
    return InputDecoration(
      labelText: label,
      isDense: true,
      filled: true,
      fillColor: palette.surface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      counterStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
        color: palette.muted,
        height: 1.5,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: palette.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: palette.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: palette.accent, width: 1.5),
      ),
    );
  }

''' +s[pos:]
p.write_text(s)
