import 'package:flutter/material.dart';
import 'package:sokoun_app/features/shared/contact/presentation/widgets/revealed_phone_card.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

class TenantPropertyOwnerCard extends StatelessWidget {
  const TenantPropertyOwnerCard({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    final avatarFallback = Icon(
      Icons.person_outline_rounded,
      color: context.appColor(AppColors.sokoonTeal),
      size: 22.r,
    );
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        spacing: 12.h,
        children: [
          Row(
            spacing: 12.w,
            children: [
              Container(
                width: 44.r,
                height: 44.r,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.tealAlpha13,
                  borderRadius: BorderRadius.circular(22.r),
                ),
                child: ExcludeSemantics(
                  child: property.ownerAvatar.trim().isEmpty
                      ? avatarFallback
                      : CachedImage(
                          url: property.ownerAvatar,
                          width: 44.r,
                          height: 44.r,
                          boxShape: BoxShape.circle,
                          fit: BoxFit.cover,
                          placeHolder: avatarFallback,
                        ),
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 4.h,
                  children: [
                    Row(
                      spacing: 6.w,
                      children: [
                        Flexible(
                          child: AppText(
                            property.ownerName,
                            style: AppTextStyles.bold14.copyWith(
                              color: context.appColor(AppColors.sokoonNavy),
                              fontSize: 14.sp,
                              height: 1.45,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (property.isOwnerVerified)
                          Container(
                            padding: EdgeInsets.symmetric(
                              horizontal: 6.w,
                              vertical: 2.h,
                            ),
                            decoration: BoxDecoration(
                              color: context.appColor(
                                AppColors.sokoonTeal,
                                surface: true,
                              ),
                              borderRadius: BorderRadius.circular(6.r),
                            ),
                            child: AppText(
                              LocaleKeys.verified,
                              style: AppTextStyles.extraBold.copyWith(
                                color: AppColors.white,
                                fontSize: 10.sp,
                              ),
                            ),
                          ),
                      ],
                    ),
                    AppText(
                      property.ownerMeta,
                      style: AppTextStyles.medium12.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (property.ownerPhone.isNotEmpty)
            RevealedPhoneCard(phoneNumber: property.ownerPhone)
          else
            Container(
              padding: EdgeInsets.all(10.w),
              decoration: BoxDecoration(
                color: context.appColor(AppColors.grayOffWhite, surface: true),
                borderRadius: BorderRadius.circular(10.r),
              ),
              child: Row(
                spacing: 8.w,
                children: [
                  Icon(
                    Icons.lock_outline_rounded,
                    color: context.appColor(AppColors.sokoonGray),
                    size: 16.r,
                  ),
                  Expanded(
                    child: AppText(
                      LocaleKeys.tenantPropertyDetailsPhonePrivacy,
                      style: AppTextStyles.medium11.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        fontSize: 11.sp,
                        height: 1.45,
                      ),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
