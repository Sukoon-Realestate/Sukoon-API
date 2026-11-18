from pathlib import Path
base=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/help')
p=base/'support_help_header.dart'
p.write_text('''part of '../../../imports.dart';

class SupportHelpHeader extends StatelessWidget {
  const SupportHelpHeader({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            workspace.isOwner ? LocaleKeys.supportOwnerIntro : LocaleKeys.supportTenantIntro,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: palette.muted, height: 1.5),
          ),
          const SizedBox(height: 16),
          DefaultButton(
            title: LocaleKeys.supportNewTicket,
            onTap: () => Go.to(SupportNewTicketScreen(workspace: workspace)),
          ),
          const SizedBox(height: 12),
          Material(
            color: palette.surface,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: BorderSide(color: palette.line),
            ),
            clipBehavior: Clip.antiAlias,
            child: Column(
              children: [
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                  leading: Icon(Icons.confirmation_number_outlined, color: palette.accent, size: 20),
                  title: AppText(LocaleKeys.supportMyTickets, style: Theme.of(context).textTheme.bodyMedium),
                  trailing: Icon(Icons.chevron_right_rounded, color: palette.muted, size: 20),
                  onTap: () => Go.to(SupportTicketsScreen(workspace: workspace)),
                ),
                Divider(height: 1, indent: 16, endIndent: 16, color: palette.line),
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                  leading: Icon(Icons.lightbulb_outline, color: palette.accent, size: 20),
                  title: AppText(LocaleKeys.uxSuggestImprovement, style: Theme.of(context).textTheme.bodyMedium),
                  trailing: Icon(Icons.chevron_right_rounded, color: palette.muted, size: 20),
                  onTap: () => Go.to(SupportNewTicketScreen(workspace: workspace, feedback: true)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
''')
p=base/'support_help_content_view.dart'
s=p.read_text().replace('padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),','padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),')
a=s.index('        Card(')
b=s.index('        16.szH,',a)
s=s[:a]+'''        Card(
          margin: EdgeInsets.zero,
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: Icon(Icons.mail_outline, size: 22, color: SokounPalette.of(context).muted),
            title: AppText(LocaleKeys.supportEmailUs, style: Theme.of(context).textTheme.titleSmall),
            subtitle: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(widget.content.email, textDirection: TextDirection.ltr,
                  style: Theme.of(context).textTheme.bodyMedium),
                if (widget.content.hours.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  AppText(widget.content.hours, style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: SokounPalette.of(context).muted, height: 1.5)),
                ],
              ],
            ),
            onTap: () => _contact(Uri(scheme: 'mailto', path: widget.content.email)),
          ),
        ),
''' +s[b:]
s=s.replace('''        controller: _search,
''','''        controller: _search,
        useGlass: false,
''',1)
p.write_text(s)
p=base/'support_faq_tile.dart'
s=p.read_text().replace('BorderRadius.circular(16.r)','BorderRadius.circular(12)')
s=s.replace('''        title: AppText(faq.question, style: AppTextStyles.bold14),''','''        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        title: AppText(faq.question, style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.w600, height: 1.5)),''')
p.write_text(s)
