from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
lib=root/'apps/sokoun_app/lib'
p=lib/'shared_widgets/sokoun_page_intro.dart'
s=p.read_text().replace('    this.showWordmark = false,', '    this.showWordmark = false,\n    this.compact = false,\n    this.showTitle = true,')
s=s.replace('  final bool showWordmark;', '  final bool showWordmark;\n  final bool compact, showTitle;')
s=s.replace('        AppText(title, style: theme.textTheme.titleLarge),', '''        if (showTitle)
          AppText(title, style: compact ? theme.textTheme.titleSmall : theme.textTheme.titleLarge),''')
s=s.replace('          SizedBox(height: 8.h),', '          if (showTitle) SizedBox(height: compact ? 6 : 8.h),')
s=s.replace('style: theme.textTheme.bodyMedium?.copyWith(', 'style: (compact ? theme.textTheme.bodySmall : theme.textTheme.bodyMedium)?.copyWith(\n              height: 1.5,')
p.write_text(s)
(lib/'shared_widgets/sokoun_settings_section.dart').write_text('''import 'package:flutter/material.dart';
import 'sokoun_palette.dart';

/// Quiet, compact grouping for related settings without changing their owners.
class SokounSettingsSection extends StatelessWidget {
  const SokounSettingsSection({super.key, this.title, this.description, required this.child});
  final String? title, description;
  final Widget child;
  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: palette.surface,
        border: Border.all(color: palette.line),
        borderRadius: BorderRadius.circular(16),
      ),
      child: DefaultTextStyle.merge(
        style: TextStyle(fontSize: 13, height: 1.5, color: palette.text, fontWeight: FontWeight.w400),
        child: ListTileTheme(
          data: ListTileThemeData(
            contentPadding: EdgeInsets.zero,
            minTileHeight: 48,
            minVerticalPadding: 6,
            horizontalTitleGap: 8,
            titleTextStyle: theme.textTheme.bodyMedium?.copyWith(color: palette.text, fontSize: 13, height: 1.5),
            subtitleTextStyle: theme.textTheme.bodySmall?.copyWith(color: palette.muted, fontSize: 12, height: 1.5),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (title != null) Text(title!, style: theme.textTheme.titleSmall?.copyWith(color: palette.text, height: 1.5)),
              if (description != null) ...[
                const SizedBox(height: 4),
                Text(description!, style: theme.textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.5)),
              ],
              if (title != null || description != null) const SizedBox(height: 12),
              child,
            ],
          ),
        ),
      ),
    );
  }
}
''')
for rel in ['features/shared/profile/presentation/widgets/settings/change_password_form.dart', 'features/shared/support/presentation/widgets/new_ticket/support_ticket_form_content.dart']:
 p=lib/rel
 s=p.read_text().replace('padding: EdgeInsets.all(20.r),','padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),')
 s=s.replace('SokounPageIntro(\n', 'SokounPageIntro(\n                                compact: true,\n                                showTitle: false,\n')
 if 'change_password' in rel:
  s=s.replace('spacing: 20.h,','spacing: 16,')
  a=s.index('                          ProfileVerificationBanner(')
  b=s.index('\n                        ],',a)
  s=s[:a]+'''                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.lock_outline_rounded, size: 16,
                                color: SokounPalette.of(context).muted),
                              const SizedBox(width: 8),
                              Expanded(child: AppText(
                                '${LocaleKeys.settingsPasswordPolicyTitle}\\n${LocaleKeys.settingsPasswordPolicyDescription}',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: SokounPalette.of(context).muted, height: 1.5),
                              )),
                            ],
                          ),''' +s[b:]
 else:
  s=s.replace('spacing: 18.h,','spacing: 14,')
  s=s.replace('minLines: 4,','minLines: 3,').replace('maxLines: 8,','maxLines: 6,')
  s=s.replace('SokounSelectionChip(\n                                        label: topic.label,', '''ChoiceChip(
                                        label: Text(topic.label),
                                        showCheckmark: false,
                                        selectedColor: SokounPalette.of(context).chip,
                                        backgroundColor: SokounPalette.of(context).surface,
                                        side: BorderSide(color: SokounPalette.of(context).line),
                                        labelStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
                                          color: SokounPalette.of(context).text, height: 1.5),
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),''')
  s=s.replace('onPressed: () =>\n                                            owner._body.value', 'onSelected: (_) =>\n                                            owner._body.value')
 p.write_text(s)
# Support barrel needs the palette for its part widget.
p=lib/'features/shared/support/imports.dart'
s=p.read_text()
if 'sokoun_palette.dart' not in s: s="import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';\n"+s
p.write_text(s)
p=lib/'features/shared/experience/presentation/widgets/data_saving_settings.dart'
s=p.read_text()
s="import 'package:sokoun_app/shared_widgets/sokoun_settings_section.dart';\n"+s
s=s.replace('''      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            LocaleKeys.exDataSaving,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          Text(LocaleKeys.exDataSavingHelp),''', '''      child: SokounSettingsSection(
        title: LocaleKeys.exDataSaving,
        description: LocaleKeys.exDataSavingHelp,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [''')
s=s.replace('''        ],
      ),
    ),''','''          ],
        ),
      ),
    ),''')
p.write_text(s)
p=lib/'features/shared/experience/presentation/screens/experience_settings_screen.dart'
s=p.read_text().replace('const Divider(),','const SizedBox(height: 16),')
s=s.replace('''          builder: (value) => Column(
            children:''', '''          builder: (value) => Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 16,
            children:''')
p.write_text(s)
p=lib/'features/shared/experience/presentation/widgets/discovery_settings.dart'
s=p.read_text()
s="import 'package:sokoun_app/shared_widgets/sokoun_settings_section.dart';\n"+s
s=s.replace('''        builder: (value) => _PrioritiesForm(''', '''        builder: (value) => SokounSettingsSection(
          title: LocaleKeys.exPriorities,
          description: LocaleKeys.exPrioritiesHelp,
          child: _PrioritiesForm(''')
s=s.replace('''        ),
      );
}''', '''          ),
        ),
      );
}''',1)
s=s.replace('''            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                LocaleKeys.exPriorities,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              Text(LocaleKeys.exPrioritiesHelp),''','''            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12,
            children: [''')
a=s.index('              for (final priority in HousingPriority.values)')
b=s.index('              for (final priority in priorities.skip(1))',a)
s=s[:a]+'''              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final priority in HousingPriority.values)
                    FilterChip(
                      label: Text(priorityLabel(priority)),
                      avatar: priorities.contains(priority)
                        ? Text('${priorities.indexOf(priority) + 1}') : null,
                      selected: priorities.contains(priority),
                      showCheckmark: false,
                      onSelected: priorities.length >= 3 && !priorities.contains(priority)
                        ? null
                        : (v) => _priorities.value = v
                          ? [...priorities, priority]
                          : priorities.where((p) => p != priority).toList(),
                    ),
                ],
              ),
''' +s[b:]
p.write_text(s)
# Sync remains in its own visible group with its current controller and gates.
p=lib/'features/shared/experience/presentation/widgets/personal_sync_settings.dart'
s=p.read_text()
s="import 'package:sokoun_app/shared_widgets/sokoun_settings_section.dart';\n"+s
s=s.replace('''    builder: (_, state) => Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Divider(),
        Text(LocaleKeys.exSync, style: Theme.of(context).textTheme.titleMedium),
        Text(LocaleKeys.exSyncHelp),''','''    builder: (_, state) => SokounSettingsSection(
      title: LocaleKeys.exSync,
      description: LocaleKeys.exSyncHelp,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [''')
s=s.replace('''      ],
    ),
  );''','''        ],
      ),
    ),
  );''')
p.write_text(s)
