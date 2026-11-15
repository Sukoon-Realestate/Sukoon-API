from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/visit_decisions/presentation/widgets/viewing_day_plan_content.dart')
s=p.read_text()
s="import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';\n"+s
s=s.replace('''    final data = state.data, query = data.query;''','''    final data = state.data, query = data.query;
    final palette = SokounPalette.of(context);
    final theme = Theme.of(context);
    final fieldStyle = theme.textTheme.bodyMedium?.copyWith(
      fontSize: 14, fontWeight: FontWeight.w500, color: palette.text, height: 1.5);
    InputDecoration fieldDecoration(String label) => InputDecoration(
      labelText: label,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      labelStyle: theme.textTheme.bodySmall?.copyWith(color: palette.muted),
    );''')
s=s.replace('padding: const EdgeInsets.all(20),','padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),',1)
s=s.replace('''        Text(LocaleKeys.dayPlanHelp),''','''        Text(LocaleKeys.dayPlanHelp,
          style: theme.textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.6)),
        const SizedBox(height: 16),''')
s=s.replace('''        ListTile(
          title: Text(query.date),
          subtitle: const Text('Africa/Cairo'),
          trailing: const Icon(Icons.calendar_month),''','''        ListTile(
          contentPadding: EdgeInsets.zero,
          minVerticalPadding: 8,
          leading: Icon(Icons.calendar_today_outlined, size: 22, color: palette.accent),
          title: Text(DateFormat.yMMMMd(Localizations.localeOf(context).languageCode).format(query.day),
            style: theme.textTheme.titleSmall?.copyWith(color: palette.text)),
          subtitle: Text('Africa/Cairo', style: theme.textTheme.bodySmall?.copyWith(color: palette.muted)),
          trailing: Icon(Icons.expand_more_rounded, color: palette.muted),''')
s=s.replace('''          decoration: InputDecoration(
            labelText: LocaleKeys.dayPlanViewingDuration,
          ),''','''          style: fieldStyle,
          decoration: fieldDecoration(LocaleKeys.dayPlanViewingDuration),''')
s=s.replace('''          decoration: InputDecoration(labelText: LocaleKeys.dayPlanBuffer),''','''          style: fieldStyle,
          decoration: fieldDecoration(LocaleKeys.dayPlanBuffer),''')
s=s.replace('''          decoration: InputDecoration(labelText: LocaleKeys.dayPlanMode),''','''          style: fieldStyle,
          decoration: fieldDecoration(LocaleKeys.dayPlanMode),''')
s=s.replace('''        TextButton.icon(
          icon: const Icon(Icons.location_on_outlined),''','''        const SizedBox(height: 12),
        TextButton.icon(
          style: TextButton.styleFrom(
            alignment: AlignmentDirectional.centerStart,
            minimumSize: const Size(0, 48),
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 10)),
          icon: const Icon(Icons.location_on_outlined, size: 20),''',1)
s=s.replace('''        FilledButton(
          onPressed: state.isLoading ? null : cubit.load,''','''        const SizedBox(height: 12),
        FilledButton(
          style: FilledButton.styleFrom(minimumSize: const Size(0, 48)),
          onPressed: state.isLoading ? null : cubit.load,''')
s=s.replace('''          if (data.plan!.visits.isEmpty) Text(LocaleKeys.dayPlanEmpty),''','''          const SizedBox(height: 20),
          if (data.plan!.visits.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.event_available_outlined, size: 20, color: palette.muted),
                  const SizedBox(width: 10),
                  Expanded(child: Text(LocaleKeys.dayPlanEmpty,
                    style: theme.textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.5))),
                ],
              ),
            ),''')
p.write_text(s)
