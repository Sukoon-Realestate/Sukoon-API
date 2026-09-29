import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

class OwnerRequestCard extends StatelessWidget {
  const OwnerRequestCard({
    super.key,
    required this.requestId,
    required this.name,
    required this.details,
    this.avatarUrl,
    this.onRequestResolved,
  });

  final String requestId;
  final String name;
  final String details;
  final String? avatarUrl;
  final Future<void> Function()? onRequestResolved;

  Future<void> _openDetails() async {
    final OwnerRequestResolution? resolution =
        await Go.to<OwnerRequestResolution>(
          OwnerRequestDetailsScreen(requestId: requestId),
        );
    if (resolution != null) await onRequestResolved?.call();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: _openDetails,
        borderRadius: BorderRadius.circular(20.r),
        splashFactory: InkRipple.splashFactory,
        child: Container(
          padding: EdgeInsets.all(14.w),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(20.r),
            border: Border.all(color: AppColors.sokoonBorder),
            boxShadow: const [
              BoxShadow(
                color: AppColors.shadowBlack04,
                blurRadius: 4,
                offset: Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 38.r,
                height: 38.r,
                decoration: const BoxDecoration(
                  color: AppColors.bluePale,
                  shape: BoxShape.circle,
                ),
                child: avatarUrl?.isNotEmpty ?? false
                    ? ClipOval(
                        child: Image.network(
                          avatarUrl!,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) => Icon(
                            Icons.person_outline,
                            color: AppColors.blue,
                            size: 20.r,
                          ),
                        ),
                      )
                    : Icon(
                        Icons.person_outline,
                        color: AppColors.blue,
                        size: 20.r,
                      ),
              ),
              10.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AppText(
                      name,
                      style: AppTextStyles.bold14.copyWith(
                        color: AppColors.sokoonNavy,
                        fontSize: 14.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    3.szH,
                    AppText(
                      details,
                      style: AppTextStyles.regular12.copyWith(
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              8.szW,
              DefaultButton(
                onTap: _openDetails,
                title: LocaleKeys.ownerRequestDetailsTitle,
                color: AppColors.bluePale,
                textColor: AppColors.blue,
                borderRadius: BorderRadius.circular(10.r),
                padding: EdgeInsets.symmetric(horizontal: 8.w),
                width: 90.w,
                height: 32.h,
                textStyle: AppTextStyles.bold12.copyWith(
                  fontSize: 12.sp,
                  height: 1.45,
                ),
                isFitted: false,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
