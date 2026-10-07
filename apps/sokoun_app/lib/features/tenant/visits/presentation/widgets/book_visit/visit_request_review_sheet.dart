part of '../../../imports.dart';

class VisitRequestReviewSheet extends StatelessWidget {
  const VisitRequestReviewSheet({
    super.key,
    required this.property,
    required this.day,
    required this.time,
    this.note = '',
  });
  final VisitPropertyContent property;
  final VisitDayContent day;
  final TimeOfDay time;
  final String note;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(20),
    child: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.freeReviewVisit,
            style: AppTextStyles.bold.copyWith(fontSize: 18),
          ),
          const SizedBox(height: 16),
          if (property.selection != null)
            RentalSelectionPanel(selection: property.selection!),
          if (property.hasRentalOffers) AppText(LocaleKeys.rentalViewingOnly),
          VisitSummaryCard(
            rows: [
              (
                label: LocaleKeys.tenantVisitSummaryProperty,
                value: property.title,
              ),
              (label: LocaleKeys.tenantVisitSummaryDay, value: day.fullLabel),
              (
                label: LocaleKeys.tenantVisitSummaryTime,
                value: time.format(context),
              ),
              (
                label: LocaleKeys.tenantVisitSummaryStatus,
                value: LocaleKeys.tenantVisitPendingOwnerResponse,
              ),
            ],
          ),
          const SizedBox(height: 16),
          AppText(LocaleKeys.freeVisitPendingExplanation),
          if (note.trim().isNotEmpty) ...[
            const SizedBox(height: 12),
            AppText(note.trim()),
          ],
          const SizedBox(height: 16),
          DefaultButton(
            title: LocaleKeys.tenantVisitConfirmRequest,
            onTap: () => Go.back(true),
          ),
        ],
      ),
    ),
  );
}
