part of '../../../imports.dart';

class VisitDetailsExtra extends StatelessWidget {
  const VisitDetailsExtra({super.key, required this.details});
  final TenantVisitDetailsContent details;
  @override
  Widget build(BuildContext context) {
    final List<({String label, String value})> rows = [
      if (details.location.trim().isNotEmpty)
        (label: LocaleKeys.visitPropertyLocation, value: details.location),
      if (details.price.trim().isNotEmpty)
        (label: LocaleKeys.visitPropertyPrice, value: details.price),
      if (details.pricePeriod.trim().isNotEmpty)
        (label: LocaleKeys.visitPricePeriod, value: _period),
      if (details.bedrooms != null)
        (
          label: LocaleKeys.ownerAddPropertyBedrooms,
          value: details.bedrooms.toString(),
        ),
      if (details.visit.ownerPhone.isEmpty && details.maskedPhone.isNotEmpty)
        (label: LocaleKeys.phoneNumber, value: details.maskedPhone),
      if (details.ownerVerified)
        (label: LocaleKeys.tenantVisitOwnerLabel, value: LocaleKeys.verified),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (rows.isNotEmpty) ...[12.szH, VisitSummaryCard(rows: rows)],
        if (details.note.trim().isNotEmpty) ...[
          12.szH,
          VisitNoteCard(note: details.note),
        ],
        if (details.review != null) ...[
          12.szH,
          PropertyReviewCard(review: details.review!),
        ],
      ],
    );
  }

  String get _period => switch (details.pricePeriod) {
    'monthly' => LocaleKeys.visitMonthly,
    'daily' => LocaleKeys.visitDaily,
    'yearly' => LocaleKeys.visitYearly,
    _ => details.pricePeriod,
  };
}
