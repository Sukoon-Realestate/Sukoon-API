part of '../../imports.dart';

class OwnerPropertyRejectionScreen extends StatelessWidget {
  const OwnerPropertyRejectionScreen({super.key, required this.property});

  final OwnerPropertyContent property;

  Future<void> _editAndResubmit() async {
    final OwnerPropertyEditResult? result =
        await Go.to<OwnerPropertyEditResult>(
          OwnerEditPropertyScreen(
            property: property.copyWith(status: OwnerPropertyStatus.rejected),
          ),
        );
    if (result != null && !result.isDeleted) {
      Go.back(result.property.copyWith(status: OwnerPropertyStatus.pending));
    }
  }

  void _contactSupport(BuildContext context) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(content: AppText(LocaleKeys.ownerPropertySupportMessage)),
      );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              OwnerPropertyTopBar(
                title: LocaleKeys.ownerPropertyRejectionTitle,
              ),
              Expanded(
                child: ListView(
                  padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 24.h),
                  children: [
                    Center(
                      child: Container(
                        width: 88.r,
                        height: 88.r,
                        decoration: const BoxDecoration(
                          color: AppColors.redPale,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.error_outline_rounded,
                          color: AppColors.red,
                          size: 42.r,
                        ),
                      ),
                    ),
                    12.szH,
                    Center(
                      child: OwnerPropertyStatusBadge(
                        status: OwnerPropertyStatus.rejected,
                      ),
                    ),
                    12.szH,
                    AppText(
                      LocaleKeys.ownerPropertyRejectedHeadline,
                      color: AppColors.sokoonNavy,
                      fontSize: 22.sp,
                      fontWeight: FontWeight.w900,
                      textAlign: TextAlign.center,
                    ),
                    6.szH,
                    AppText(
                      property.title,
                      color: AppColors.sokoonGray,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w600,
                      textAlign: TextAlign.center,
                    ),
                    20.szH,
                    _RejectionSection(
                      title: LocaleKeys.ownerPropertyRejectionReasons,
                      children: [
                        _RejectionReason(
                          text: LocaleKeys.ownerPropertyReasonUnclearPhotos,
                        ),
                        10.szH,
                        _RejectionReason(
                          text: LocaleKeys.ownerPropertyReasonIncompleteInfo,
                        ),
                      ],
                    ),
                    14.szH,
                    _RejectionSection(
                      title: LocaleKeys.ownerPropertyReviewerNotes,
                      children: [
                        AppText(
                          LocaleKeys.ownerPropertyReviewerNotesDescription,
                          color: AppColors.sokoonGray,
                          fontSize: 13.sp,
                          height: 1.55,
                        ),
                      ],
                    ),
                    14.szH,
                    Container(
                      padding: EdgeInsets.all(14.w),
                      decoration: BoxDecoration(
                        color: AppColors.orangePale,
                        borderRadius: BorderRadius.circular(16.r),
                        border: Border.all(color: AppColors.yellowPale),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.info_outline_rounded,
                            color: AppColors.amber,
                            size: 21.r,
                          ),
                          9.szW,
                          Expanded(
                            child: AppText(
                              LocaleKeys.ownerPropertyRejectionWarning,
                              color: AppColors.brown,
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w700,
                              height: 1.45,
                            ),
                          ),
                        ],
                      ),
                    ),
                    22.szH,
                    DefaultButton(
                      key: const ValueKey(
                        'owner-property-rejection-edit-resubmit',
                      ),
                      title: LocaleKeys.ownerPropertyEditAndResubmit,
                      onTap: _editAndResubmit,
                      height: 50.h,
                      borderRadius: BorderRadius.circular(15.r),
                      fontWeight: FontWeight.w900,
                    ),
                    12.szH,
                    DefaultButton(
                      key: const ValueKey('owner-property-rejection-support'),
                      title: LocaleKeys.ownerPropertyContactSupport,
                      onTap: () => _contactSupport(context),
                      height: 50.h,
                      color: AppColors.white,
                      textColor: AppColors.sokoonTeal,
                      borderColor: AppColors.sokoonTeal,
                      borderRadius: BorderRadius.circular(15.r),
                      fontWeight: FontWeight.w900,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RejectionSection extends StatelessWidget {
  const _RejectionSection({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            title,
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          12.szH,
          ...children,
        ],
      ),
    );
  }
}

class _RejectionReason extends StatelessWidget {
  const _RejectionReason({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 7.r,
          height: 7.r,
          margin: EdgeInsets.only(top: 6.h),
          decoration: const BoxDecoration(
            color: AppColors.red,
            shape: BoxShape.circle,
          ),
        ),
        9.szW,
        Expanded(
          child: AppText(
            text,
            color: AppColors.sokoonGray,
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
      ],
    );
  }
}
