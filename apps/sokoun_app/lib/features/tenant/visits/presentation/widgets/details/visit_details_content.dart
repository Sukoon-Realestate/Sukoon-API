part of '../../../imports.dart';

class VisitDetailsContent extends StatelessWidget {
  const VisitDetailsContent({
    super.key,
    required this.visit,
    this.details,
    this.onCancel,
    this.onReview,
  });

  final TenantVisitContent visit;
  final TenantVisitDetailsContent? details;
  final Future<void> Function()? onCancel;
  final Future<void> Function()? onReview;

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
          if (visit.rentalSelection != null)
            RentalSelectionPanel(
              selection: visit.rentalSelection!,
              historical: true,
            ),
          if (visit.status.isAccepted && visit.ownerPhone.isNotEmpty) ...[
            12.szH,
            VisitContactCard(ownerPhone: visit.ownerPhone),
          ],
          if (details != null) VisitDetailsExtra(details: details!),
          if (details?.propertyId.isNotEmpty == true)
            PrivateViewingNotesButton(
              propertyId: details!.propertyId,
              title: visit.propertyTitle,
            ),
          14.szH,
          VisitDetailsActions(
            visit: visit,
            onCancel: onCancel,
            onReview: details?.review == null ? onReview : null,
          ),
          const SizedBox(height: 12),
          VisitCalendarButton(visit: visit),
        ],
      ),
    );
  }
}
