part of '../../../imports.dart';

class VisitCancellationDialog extends StatelessWidget {
  const VisitCancellationDialog({super.key, required this.visit});

  final TenantVisitContent visit;

  static Future<bool> confirm(
    BuildContext context,
    TenantVisitContent visit,
  ) async =>
      await showDialog<bool>(
        context: context,
        builder: (_) => VisitCancellationDialog(visit: visit),
      ) ??
      false;

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: AppText(LocaleKeys.visitCancellationTitle),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12.h,
      children: [
        AppText(visit.propertyTitle, style: AppTextStyles.bold14),
        AppText(visit.dateLabel),
        AppText(LocaleKeys.visitCancellationDescription),
      ],
    ),
    actions: [
      TextButton(
        onPressed: () => Go.back(false),
        child: AppText(LocaleKeys.visitKeepBooking),
      ),
      TextButton(
        onPressed: () => Go.back(true),
        child: AppText(
          LocaleKeys.visitConfirmCancellation,
          style: AppTextStyles.bold14.copyWith(color: AppColors.sokoonRose),
        ),
      ),
    ],
  );
}
