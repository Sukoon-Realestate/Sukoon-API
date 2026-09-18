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
  bool _isLoadingPropertyDetails = false;

  Future<void> _editAndResubmit() async {
    if (_isLoadingPropertyDetails) {
      return;
    }
    setState(() => _isLoadingPropertyDetails = true);
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
        setState(() => _isLoadingPropertyDetails = false);
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
    return Scaffold(
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
                  Container(
                    padding: EdgeInsets.all(16.w),
                    decoration: BoxDecoration(
                      color: AppColors.white,
                      borderRadius: BorderRadius.circular(18.r),
                      border: Border.all(color: AppColors.sokoonBorder),
                    ),
                    child: AppText(
                      LocaleKeys.ownerPropertyRejectionDetailsUnavailable,
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
                      height: 1.55,
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
                    title: LocaleKeys.ownerPropertyEditAndResubmit,
                    onTap: _isLoadingPropertyDetails ? null : _editAndResubmit,
                    height: 50.h,
                    borderRadius: BorderRadius.circular(15.r),
                    fontWeight: FontWeight.w900,
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
