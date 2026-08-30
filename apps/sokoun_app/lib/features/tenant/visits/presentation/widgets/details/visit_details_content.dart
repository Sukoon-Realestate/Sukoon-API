part of '../../../imports.dart';

class VisitDetailsContent extends StatelessWidget {
  const VisitDetailsContent({
    super.key,
    required this.visit,
    required this.onOpenChatPressed,
    required this.onCancelVisitPressed,
    required this.onFindAlternativePressed,
  });

  final TenantVisitContent visit;
  final VoidCallback onOpenChatPressed;
  final VoidCallback onCancelVisitPressed;
  final VoidCallback onFindAlternativePressed;

  List<({String label, String value})> get _summaryRows {
    return [
      (
        label: LocaleKeys.tenantVisitSummaryProperty,
        value: visit.propertyTitle,
      ),
      (label: LocaleKeys.tenantVisitSummaryDay, value: visit.day),
      (label: LocaleKeys.tenantVisitSummaryTime, value: visit.time),
      (
        label: LocaleKeys.tenantVisitSummaryStatus,
        value: visit.resolvedStatusText,
      ),
      if (visit.ownerName.isNotEmpty)
        (label: LocaleKeys.tenantVisitOwnerLabel, value: visit.ownerName),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          VisitStatusHeader(visit: visit),
          VisitSummaryCard(rows: _summaryRows),
          if (visit.status.isAccepted && visit.ownerPhone.isNotEmpty) ...[
            12.szH,
            VisitContactCard(ownerPhone: visit.ownerPhone),
          ],
          14.szH,
          VisitDetailsActions(
            status: visit.status,
            onOpenChatPressed: onOpenChatPressed,
            onCancelVisitPressed: onCancelVisitPressed,
            onFindAlternativePressed: onFindAlternativePressed,
          ),
        ],
      ),
    );
  }
}
