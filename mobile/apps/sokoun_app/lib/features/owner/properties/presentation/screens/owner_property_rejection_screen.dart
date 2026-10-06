part of '../../imports.dart';

class OwnerPropertyRejectionScreen extends StatefulWidget {
  const OwnerPropertyRejectionScreen({super.key, required this.property});

  final OwnerPropertyContent property;

  @override
  State<OwnerPropertyRejectionScreen> createState() =>
      _OwnerPropertyRejectionScreenState();
}

class _OwnerPropertyRejectionScreenState
    extends State<OwnerPropertyRejectionScreen> {
  final ValueNotifier<bool> _isLoadingPropertyDetails = ValueNotifier<bool>(
    false,
  );

  @override
  void dispose() {
    _isLoadingPropertyDetails.dispose();
    super.dispose();
  }

  Future<void> _editAndResubmit() async {
    if (_isLoadingPropertyDetails.value) {
      return;
    }
    _isLoadingPropertyDetails.value = true;
    final PropertyDetailsCubit cubit = PropertyDetailsCubit();
    PropertyDetailsModel? details;
    try {
      await cubit.getPropertyDetails(widget.property.id);
      if (cubit.state.isSuccess || cubit.state.data.id.isNotEmpty) {
        details = cubit.state.data;
      }
    } finally {
      await cubit.close();
      if (mounted) {
        _isLoadingPropertyDetails.value = false;
      }
    }
    if (details == null || !mounted) {
      return;
    }
    final PropertyDetailsModel? updated = await Go.to<PropertyDetailsModel>(
      OwnerPropertyFlowScreen(property: details),
    );
    if (updated != null) {
      Go.back(updated);
    }
  }

  @override
  Widget build(BuildContext context) {
    final OwnerPropertyContent property = widget.property;
    return AppScaffold(
      title: LocaleKeys.ownerPropertyRejectionTitle,
      showBackButton: true,
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 24.h),
          children: [
            Container(
              width: 88.r,
              height: 88.r,
              decoration: BoxDecoration(
                color: context.appColor(AppColors.redPale, surface: true),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.error_outline_rounded,
                color: context.appColor(AppColors.red),
                size: 42.r,
              ),
            ).centerWidget,
            12.szH,
            OwnerPropertyStatusBadge(
              status: OwnerPropertyStatus.rejected,
            ).centerWidget,
            12.szH,
            AppText(
              LocaleKeys.ownerPropertyRejectedHeadline,
              style: AppTextStyles.bold.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 22.sp,
              ),
              textAlign: TextAlign.center,
            ),
            6.szH,
            AppText(
              property.title,
              style: AppTextStyles.semiBold.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 14.sp,
              ),
              textAlign: TextAlign.center,
            ),
            20.szH,
            Container(
              padding: EdgeInsets.all(16.w),
              decoration: BoxDecoration(
                color: context.appColor(AppColors.white, surface: true),
                borderRadius: BorderRadius.circular(18.r),
                border: Border.all(
                  color: context.appColor(AppColors.sokoonBorder),
                ),
              ),
              child: AppText(
                property.rejectionReason.trim().isEmpty
                    ? LocaleKeys.ownerPropertyRejectionDetailsUnavailable
                    : property.rejectionReason,
                style: AppTextStyles.regular13.copyWith(
                  color: context.appColor(AppColors.sokoonGray),
                  fontSize: 13.sp,
                  height: 1.55,
                ),
              ),
            ),
            14.szH,
            Container(
              padding: EdgeInsets.all(14.w),
              decoration: BoxDecoration(
                color: context.appColor(AppColors.orangePale, surface: true),
                borderRadius: BorderRadius.circular(16.r),
                border: Border.all(
                  color: context.appColor(AppColors.yellowPale, surface: true),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 9.w,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    color: context.appColor(AppColors.amber),
                    size: 21.r,
                  ),
                  Expanded(
                    child: AppText(
                      LocaleKeys.ownerPropertyRejectionWarning,
                      style: AppTextStyles.bold12.copyWith(
                        color: context.appColor(AppColors.brown),
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            22.szH,
            ValueListenableBuilder<bool>(
              valueListenable: _isLoadingPropertyDetails,
              builder: (context, isLoading, _) => DefaultButton(
                title: LocaleKeys.ownerPropertyEditAndResubmit,
                onTap: isLoading ? null : _editAndResubmit,
                height: 50.h,
                borderRadius: BorderRadius.circular(15.r),
                textStyle: AppTextStyles.bold13.copyWith(
                  fontSize: FontSize.s13,
                  height: 1.45,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
