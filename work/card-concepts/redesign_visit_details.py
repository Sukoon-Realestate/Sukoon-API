from pathlib import Path
root = Path('/Users/demo23home/code/sukoon/sokoun')
base = root / 'apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/details'
p = base / 'visit_details_content.dart'
s = p.read_text()
s = s.replace('''      (
        label: LocaleKeys.tenantVisitSummaryProperty,
        value: visit.propertyTitle,
      ),
      (
        label: LocaleKeys.tenantVisitSummaryStatus,
        value: visit.resolvedStatusText,
      ),
''', '')
a = s.index('            const ExplainFeatureButton(),')
b = s.index('            if (visit.stayPreferences.enabled)', a)
s = s[:a] + '''            GuideTarget(
              id: 'VisitStatus',
              child: VisitStatusHeader(visit: visit),
            ),
            16.szH,
            GuideTarget(
              id: 'Visit',
              child: _VisitOverview(visit: visit, rows: _summaryRows),
            ),
            if (fresh && (visit.id.isNotEmpty || visit.propertyId.isNotEmpty)) ...[
              16.szH,
              _VisitTools(visit: visit, onRefresh: onRefresh),
            ],
''' + s[b:]
s = s.replace('padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),', 'padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),')
s += '''
class _VisitOverview extends StatelessWidget {
  const _VisitOverview({required this.visit, required this.rows});
  final TenantVisitContent visit;
  final List<({String label, String value})> rows;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: context.appColor(AppColors.white, surface: true),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          LocaleKeys.tenantVisitSummaryProperty,
          style: AppTextStyles.regular12.copyWith(
            color: context.appColor(AppColors.sokoonMuted),
          ),
        ),
        const SizedBox(height: 6),
        AppText(
          visit.propertyTitle,
          style: AppTextStyles.bold14.copyWith(
            color: context.appColor(AppColors.sokoonNavy),
            height: 1.5,
          ),
        ),
        if (rows.isNotEmpty) ...[
          const SizedBox(height: 12),
          Divider(height: 1, color: context.appColor(AppColors.sokoonBorder)),
          const SizedBox(height: 12),
          for (final row in rows)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AppText(
                    row.label,
                    style: AppTextStyles.regular12.copyWith(
                      color: context.appColor(AppColors.sokoonMuted),
                    ),
                  ),
                  const SizedBox(height: 2),
                  AppText(
                    row.value,
                    style: AppTextStyles.medium13.copyWith(
                      color: context.appColor(AppColors.sokoonNavy),
                      height: 1.45,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ],
    ),
  );
}

class _VisitTools extends StatelessWidget {
  const _VisitTools({required this.visit, this.onRefresh});
  final TenantVisitContent visit;
  final Future<void> Function()? onRefresh;

  @override
  Widget build(BuildContext context) {
    final workspace = WorkspaceCubit.instance.state.workspace;
    final individual = workspace == AppWorkspace.individual;
    final style = TextButton.styleFrom(
      foregroundColor: context.appColor(AppColors.sokoonNavy),
      alignment: AlignmentDirectional.centerStart,
      minimumSize: const Size(0, 48),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      textStyle: AppTextStyles.medium13.copyWith(height: 1.5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: AppText(
                LocaleKeys.toolsTitle,
                style: AppTextStyles.bold14.copyWith(
                  color: context.appColor(AppColors.sokoonNavy),
                ),
              ),
            ),
            const ExplainFeatureButton(),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: context.appColor(AppColors.white, surface: true),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
          ),
          child: TextButtonTheme(
            data: TextButtonThemeData(style: style),
            child: OutlinedButtonTheme(
              data: OutlinedButtonThemeData(
                style: style.copyWith(side: const WidgetStatePropertyAll(BorderSide.none)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (individual && visit.id.isNotEmpty) ...[
                    ViewingArrivalEntry(visitId: visit.id, workspace: 'individual'),
                    ViewingTimesEntry(
                      visitId: visit.id,
                      workspace: 'individual',
                      refresh: onRefresh,
                    ),
                    if (visit.status.isAccepted && visit.visitDate.isNotEmpty && visit.visitTime.isNotEmpty)
                      ViewingDelayEntry(visitId: visit.id),
                  ],
                  if (visit.id.isNotEmpty)
                    ViewingCalendarButton(visitId: visit.id, workspace: workspace),
                  if (visit.propertyId.isNotEmpty)
                    VisitChecklistButton(visit: visit),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
'''
p.write_text(s)
p = base / 'visit_status_header.dart'
s = p.read_text()
a = s.index('    return Column(')
s = s[:a] + '''    final foreground = context.appColor(visit.status.foregroundColor);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: context.appColor(visit.status.backgroundColor, surface: true),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Icon(visit.status.statusIcon, color: foreground, size: 26),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  _title,
                  style: AppTextStyles.bold14.copyWith(
                    color: foreground,
                    fontSize: 16.sp,
                    height: 1.5,
                  ),
                ),
                if (visit.resolvedStatusText != _title) ...[
                  const SizedBox(height: 4),
                  AppText(
                    visit.resolvedStatusText,
                    style: AppTextStyles.regular12.copyWith(
                      color: foreground,
                      height: 1.5,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
'''
p.write_text(s)
p = root / 'docs/ui-refactor/REFERENCE-ADAPTATION.md'
s = p.read_text()
s += '''\n\n## Visit details cleanup — 2026-11-15\n\n| Existing capability | Revised placement and outcome |\n| --- | --- |\n| Visit status and summary | Compact status banner first, then a property heading with untruncated owner/day/time metadata; status is no longer repeated in a summary row. Existing guide targets remain attached. |\n| Arrival card, appointment negotiation, accepted-visit delay, device calendar and checklist | One visible Tools panel below the summary, using consistent leading-aligned icon rows and 48-point minimum targets. All original freshness, workspace, identity, date and calendar capability gates remain. Existing routes, calendar sheet, checklist persistence and return refresh remain owned by their original widgets. |\n| Explain this screen | Beside the Tools heading, preserving the original guide readiness and replay guards. |\n| Rental terms, stay preferences, decision/reassignment, notes, reviews, privacy, chat, cancellation and rating | Remain in the scrollable details flow with their original data, command ownership, state and permission gates. |\n'''
p.write_text(s)
