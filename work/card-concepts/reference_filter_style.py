from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib')
p=root/'shared_widgets/sokoun_filter_style.dart'
s=p.read_text().replace('Radius.circular(12)', 'Radius.circular(999)')
s=s.replace('return palette.disabled;', 'return Colors.transparent;')
s=s.replace('return selected ? palette.action : palette.surface;', 'return selected ? palette.chip : Colors.transparent;')
s=s.replace('return selected ? palette.onAction : palette.text;', 'return selected ? palette.accent : palette.muted;')
a=s.index('        final focused = states.contains(WidgetState.focused);')
b=s.index('\n      }),',a)
s=s[:a]+'''        return BorderSide(
          width: 2,
          color: states.contains(WidgetState.focused)
              ? palette.focus : Colors.transparent,
        );''' +s[b:]
s=s.replace('final foreground = selected ? palette.onAction : palette.accent;', 'final foreground = palette.accent;')
p.write_text(s)
p=root/'shared_widgets/sokoun_selection_chip.dart'
s=p.read_text().replace('this.showCheck = true', 'this.showCheck = false')
a=s.index('        final fill = Color.lerp(')
b=s.index('        return MergeSemantics(',a)
s=s[:a]+'''        final fill = palette.chip.withValues(alpha: value);
        final foreground = Color.lerp(palette.muted, palette.accent, value)!;
''' +s[b:]
p.write_text(s)
p=root/'shared_widgets/sokoun_theme.dart'
s=p.read_text()
a=s.index('    final chipForeground = WidgetStateColor.resolveWith(')
b=s.index('\n    return ThemeData(',a)
s=s[:a]+'''    final chipForeground = WidgetStateColor.resolveWith((states) {
      if (states.contains(WidgetState.disabled)) return tokens.disabledText;
      return states.contains(WidgetState.selected) ? tokens.accent : tokens.muted;
    });''' +s[b:]
a=s.index('      chipTheme: ChipThemeData(')
b=s.index('      textButtonTheme:',a)
s=s[:a]+'''      chipTheme: ChipThemeData(
        backgroundColor: Colors.transparent,
        selectedColor: tokens.chip,
        disabledColor: Colors.transparent,
        side: WidgetStateBorderSide.resolveWith(
          (states) => BorderSide(
            width: 2,
            color: states.contains(WidgetState.focused) ? tokens.focus : Colors.transparent,
          ),
        ),
        shape: const RoundedRectangleBorder(borderRadius: SokounFilterStyle.radius),
        labelStyle: text(AppTextStyles.medium14, color: chipForeground),
        secondaryLabelStyle: text(AppTextStyles.medium14, color: chipForeground),
        checkmarkColor: tokens.accent,
        deleteIconColor: chipForeground,
        showCheckmark: false,
        padding: SokounFilterStyle.padding,
        labelPadding: EdgeInsets.zero,
        materialTapTargetSize: MaterialTapTargetSize.padded,
      ),
''' +s[b:]
p.write_text(s)
# Remove local visual overrides so theme focus/selection states stay authoritative.
for rel in [
 'features/tenant/home/presentation/widgets/tenant_filter/filter_chip_wrap.dart',
 'features/shared/experience/presentation/widgets/discovery_settings.dart',
 'features/shared/support/presentation/widgets/new_ticket/support_ticket_form_content.dart',
]:
 p=root/rel
 s=p.read_text()
 import re
 s=re.sub(r'^\s*(?:selectedColor|backgroundColor): SokounPalette\.of\(\s*context,?\s*\)\.(?:chip|surface),\n', '\n', s, flags=re.M)
 s=re.sub(r'^\s*side: BorderSide\(\s*color: SokounPalette\.of\(\s*context,?\s*\)\.line,?\s*\),\n', '\n', s, flags=re.M)
 p.write_text(s)
p=root/'shared_widgets/sokoun_filter_picker.dart'
s=p.read_text()
a=s.index('              style: quiet\n')
b=s.index('              child: Row(',a)
s=s[:a]+'''              style: SokounFilterStyle.resolve(context, selected: active),
''' +s[b:]
s=s.replace('''color: active && !quiet
                                    ? palette.onAction
                                    : palette.muted,''','''color: palette.muted,''')
s=s.replace('palette.onAction', 'palette.accent')
p.write_text(s)
