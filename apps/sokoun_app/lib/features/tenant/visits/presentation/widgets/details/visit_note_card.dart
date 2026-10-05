part of '../../../imports.dart';

class VisitNoteCard extends StatelessWidget {
  const VisitNoteCard({super.key, required this.note});
  final String note;
  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.all(16.r),
    decoration: BoxDecoration(
      color: context.appColor(AppColors.white, surface: true),
      borderRadius: BorderRadius.circular(16.r),
      border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 8.h,
      children: [
        AppText(
          LocaleKeys.ownerVisitTenantNoteTitle,
          style: AppTextStyles.bold14,
        ),
        AppText(note, style: AppTextStyles.regular14.copyWith(height: 1.5)),
      ],
    ),
  );
}
