part of '../../../imports.dart';

class OwnerRequestDetailsContent extends StatelessWidget {
  const OwnerRequestDetailsContent({
    super.key,
    required this.request,
    required this.actions,
  });

  final OwnerVisitRequestDetailsContent request;
  final Widget actions;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          OwnerRequestInfoCard(request: request),
          if (request.note.isNotEmpty) ...[
            12.szH,
            _OwnerTenantNoteCard(note: request.note),
          ],
          12.szH,
          OwnerRequestPrivacyBanner(
            message: request.tenant.displayPhoneNotice.isNotEmpty
                ? request.tenant.displayPhoneNotice
                : LocaleKeys.ownerVisitTenantPhoneHidden,
          ),
          16.szH,
          actions,
        ],
      ),
    );
  }
}

class _OwnerTenantNoteCard extends StatelessWidget {
  const _OwnerTenantNoteCard({required this.note});

  final String note;

  @override
  Widget build(BuildContext context) {
    return Container(
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
            style: AppTextStyles.bold14.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
          AppText(
            note,
            style: AppTextStyles.regular14.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 14.sp,
              height: 1.45,
            ),
            maxLines: 4,
          ),
        ],
      ),
    );
  }
}
