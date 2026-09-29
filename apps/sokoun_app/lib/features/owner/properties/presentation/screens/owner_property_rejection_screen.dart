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
      OwnerEditPropertyScreen(property: details),
    );
    if (updated != null) {
      Go.back(updated);
    }
  }

  @override
  Widget build(BuildContext context) {
    final OwnerPropertyContent property = widget.property;
    return AppScaffold(
      showBackButton: false,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Column(
          children: [
            OwnerPropertyTopBar(title: LocaleKeys.ownerPropertyRejectionTitle),
            Expanded(
              child: ListView(
                padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 24.h),
                children: [
                  Container(
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
                  ).centerWidget,
                  12.szH,
                  OwnerPropertyStatusBadge(
                    status: OwnerPropertyStatus.rejected,
                  ).centerWidget,
                  12.szH,
                  AppText(
                    LocaleKeys.ownerPropertyRejectedHeadline,
                    style: AppTextStyles.bold.copyWith(
                      color: AppColors.sokoonNavy,
                      fontSize: 22.sp,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  6.szH,
                  AppText(
                    property.title,
                    style: AppTextStyles.semiBold.copyWith(
                      color: AppColors.sokoonGray,
                      fontSize: 14.sp,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  20.szH,
                  Container(
                    padding: EdgeInsets.all(16.w),
                    decoration: BoxDecoration(
                      color: AppColors.white,
                      borderRadius: BorderRadius.circular(18.r),
                      border: Border.all(color: AppColors.sokoonBorder),
                    ),
                    child: AppText(
                      LocaleKeys.ownerPropertyRejectionDetailsUnavailable,
                      style: AppTextStyles.regular13.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 13.sp,
                        height: 1.55,
                      ),
                    ),
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
                            style: AppTextStyles.bold12.copyWith(
                              color: AppColors.brown,
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
          ],
        ),
      ),
    );
  }
}
