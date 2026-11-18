from pathlib import Path
base=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets')
p=base/'reputation_section_card.dart'
p.write_text('''import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';
import '../../data/models/reputation_section.dart';
import 'review_status_text.dart';

class ReputationSectionCard extends StatelessWidget {
  const ReputationSectionCard({super.key, required this.section});
  final ReputationSection section;

  @override
  Widget build(BuildContext context) {
    final palette = SokounPalette.of(context);
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: palette.muted, height: 1.5);
    return Card(
      margin: EdgeInsets.zero,
      elevation: 0,
      color: palette.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: palette.line),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: AppText(section.label,
                  style: theme.textTheme.titleSmall?.copyWith(color: palette.text, height: 1.5))),
                if (section.score != null) ...[
                  const SizedBox(width: 12),
                  Semantics(
                    label: '${section.score} ${LocaleKeys.ratingOutOfFive}',
                    excludeSemantics: true,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(color: palette.chip, borderRadius: BorderRadius.circular(8)),
                      child: Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.star_rounded, size: 16, color: palette.accent),
                        const SizedBox(width: 4),
                        Text('${section.score}/5', style: theme.textTheme.labelMedium?.copyWith(color: palette.accent)),
                      ]),
                    ),
                  ),
                ],
              ],
            ),
            if (section.month.isNotEmpty) ...[
              const SizedBox(height: 4),
              AppText(section.month, style: muted),
            ],
            const SizedBox(height: 12),
            AppText(
              section.verificationBasis == 'legacy_unverified'
                ? LocaleKeys.ratingLegacy
                : section.verificationBasis == 'recorded_viewing'
                  ? LocaleKeys.ratingRecordedViewing : LocaleKeys.ratingRecordedStay,
              style: muted,
            ),
            if (section.managementChanged) ...[
              const SizedBox(height: 6),
              AppText(LocaleKeys.ratingManagementChanged, style: muted),
            ],
            if (section.comment.isNotEmpty) ...[
              const SizedBox(height: 12),
              AppText(section.comment, style: theme.textTheme.bodyMedium?.copyWith(color: palette.text, height: 1.65)),
            ],
            if (section.gateState == 'waiting') ...[
              const SizedBox(height: 8),
              AppText(LocaleKeys.ratingWaiting, style: muted),
            ],
            if (section.contentState.isNotEmpty) ...[
              const SizedBox(height: 8),
              AppText(reviewStatusText(section.contentState), style: muted),
            ],
            if (section.reply.isNotEmpty) ...[
              const SizedBox(height: 12),
              Divider(height: 1, color: palette.line),
              const SizedBox(height: 12),
              AppText(LocaleKeys.ratingReply, style: theme.textTheme.labelMedium),
              const SizedBox(height: 6),
              AppText(section.reply, style: theme.textTheme.bodyMedium?.copyWith(color: palette.text, height: 1.65)),
            ],
          ],
        ),
      ),
    );
  }
}
''')
p=base/'reputation_sections_list.dart'
s=p.read_text().replace("import 'package:flutter_screenutil/flutter_screenutil.dart';\n",'')
s=s.replace('padding: EdgeInsets.all(20.r),','padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),')
s=s.replace('''          if (widget.introduction != null) widget.introduction!,''','''          if (widget.introduction != null) ...[
            widget.introduction!,
            const SizedBox(height: 20),
          ],''')
s=s.replace('''          SokounPageIntro(
            title:''','''          SokounPageIntro(
            compact: true,
            title:''')
s=s.replace('''    itemBuilder: (_, __, ___, item) => InkWell(
      onTap: () => Go.to(ReputationDetailScreen(sectionId: item.id)),
      child: ReputationSectionCard(section: item),
    ),''','''    itemBuilder: (_, __, ___, item) => Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => Go.to(ReputationDetailScreen(sectionId: item.id)),
        child: ReputationSectionCard(section: item),
      ),
    ),''')
p.write_text(s)
p=base/'reputation_summary_panel.dart'
s=p.read_text()
s=s.replace('''    initiallyExpanded: initiallyExpanded || value.payment != null,''','''    tilePadding: EdgeInsets.zero,
    childrenPadding: const EdgeInsets.only(top: 8, bottom: 8),
    shape: const Border(),
    collapsedShape: const Border(),
    initiallyExpanded: initiallyExpanded || value.payment != null,''')
p.write_text(s)
