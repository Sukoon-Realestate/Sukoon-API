part of '../../../imports.dart';

class OwnerRequestDetailsContent extends StatelessWidget {
  const OwnerRequestDetailsContent({
    super.key,
    required this.request,
    required this.onAcceptPressed,
    required this.onRejectPressed,
    required this.onChatPressed,
  });

  final OwnerVisitRequestContent request;
  final VoidCallback onAcceptPressed;
  final VoidCallback onRejectPressed;
  final VoidCallback onChatPressed;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          OwnerRequestInfoCard(request: request),
          12.szH,
          _OwnerTenantNoteCard(note: request.tenantNote),
          12.szH,
          OwnerRequestPrivacyBanner(
            message: LocaleKeys.ownerVisitTenantPhoneHidden,
          ),
          16.szH,
          if (request.status.canDecide) ...[
            DefaultButton(
              key: const ValueKey('owner-request-accept'),
              onTap: onAcceptPressed,
              title: LocaleKeys.ownerVisitAcceptWithCheck,
              color: AppColors.green,
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(16.r),
              height: 52.h,
              fontSize: 15.sp,
              fontWeight: FontWeight.w900,
            ),
            12.szH,
            DefaultButton(
              key: const ValueKey('owner-request-reject'),
              onTap: onRejectPressed,
              title: LocaleKeys.ownerVisitRejectRequest,
              color: AppColors.white,
              textColor: AppColors.red,
              borderColor: AppColors.red,
              borderRadius: BorderRadius.circular(16.r),
              height: 50.h,
              fontSize: 14.sp,
              fontWeight: FontWeight.w900,
            ),
            12.szH,
          ],
          DefaultButton(
            key: const ValueKey('owner-request-open-chat'),
            onTap: onChatPressed,
            title: LocaleKeys.ownerVisitOpenChat,
            color: AppColors.bluePale,
            textColor: AppColors.blue,
            borderRadius: BorderRadius.circular(16.r),
            height: 50.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
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
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.ownerVisitTenantNoteTitle,
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          8.szH,
          AppText(
            note,
            color: AppColors.sokoonGray,
            fontSize: 14.sp,
            fontWeight: FontWeight.w400,
            maxLines: 4,
          ),
        ],
      ),
    );
  }
}
