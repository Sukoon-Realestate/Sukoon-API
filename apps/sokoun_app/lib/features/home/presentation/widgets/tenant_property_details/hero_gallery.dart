import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

class TenantPropertyHeroGallery extends StatelessWidget {
  const TenantPropertyHeroGallery({
    super.key,
    required this.property,
    required this.isSaved,
    required this.onBack,
    required this.onShare,
    required this.onSave,
    required this.onPhotosTap,
  });

  final TenantPropertyDetailsContent property;
  final bool isSaved;
  final VoidCallback onBack;
  final VoidCallback onShare;
  final VoidCallback onSave;
  final ValueChanged<int> onPhotosTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 258.h,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
          colors: [AppColors.tealDark, AppColors.sokoonTeal],
        ),
      ),
      child: Stack(
        children: [
          Center(
            child: Icon(
              Icons.apartment_outlined,
              color: AppColors.whiteAlpha40,
              size: 62.r,
            ),
          ),
          PositionedDirectional(
            top: 14.h,
            start: 14.w,
            end: 14.w,
            child: Row(
              textDirection: TextDirection.ltr,
              children: [
                _HeroIconButton(
                  icon: Icons.arrow_back_ios_new_rounded,
                  onTap: onBack,
                ),
                const Spacer(),
                _HeroIconButton(icon: Icons.ios_share_rounded, onTap: onShare),
                8.szW,
                _HeroIconButton(
                  icon: isSaved
                      ? Icons.favorite_rounded
                      : Icons.favorite_border_rounded,
                  onTap: onSave,
                ),
              ],
            ),
          ),
          PositionedDirectional(
            bottom: 76.h,
            start: 14.w,
            child: Row(
              children: [
                if (property.isVerified)
                  const _HeroPill(
                    label: 'موثّق ✓',
                    color: AppColors.sokoonTeal,
                    textColor: AppColors.white,
                  ),
                8.szW,
                _HeroPill(
                  label: '${property.photoLabels.length + 3} صورة',
                  color: AppColors.blackAlpha45,
                  textColor: AppColors.white,
                ),
              ],
            ),
          ),
          PositionedDirectional(
            bottom: 0,
            start: 0,
            end: 0,
            child: Container(
              height: 64.h,
              color: AppColors.slate,
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                reverse: true,
                itemBuilder: (context, index) {
                  final color =
                      property.imageColors[index % property.imageColors.length];
                  return GestureDetector(
                    onTap: () => onPhotosTap(index),
                    behavior: HitTestBehavior.opaque,
                    child: Container(
                      width: index == 0 ? 64.w : 58.w,
                      decoration: BoxDecoration(
                        color: color,
                        borderRadius: BorderRadius.circular(10.r),
                        border: index == 0
                            ? Border.all(color: AppColors.white, width: 2)
                            : null,
                      ),
                      child: index == 5
                          ? Center(
                              child: AppText(
                                '+7\nصور',
                                color: AppColors.white,
                                fontSize: 11.sp,
                                fontWeight: FontWeight.w900,
                                textAlign: TextAlign.center,
                              ),
                            )
                          : null,
                    ),
                  );
                },
                separatorBuilder: (context, index) => 8.szW,
                itemCount: 6,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroIconButton extends StatelessWidget {
  const _HeroIconButton({required this.icon, required this.onTap});

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: 36.r,
        height: 36.r,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.blackAlpha35,
          borderRadius: BorderRadius.circular(18.r),
        ),
        child: Icon(icon, color: AppColors.white, size: 18.r),
      ),
    );
  }
}

class _HeroPill extends StatelessWidget {
  const _HeroPill({
    required this.label,
    required this.color,
    required this.textColor,
  });

  final String label;
  final Color color;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 5.h),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: AppText(
        label,
        color: textColor,
        fontSize: 11.sp,
        fontWeight: FontWeight.w800,
      ),
    );
  }
}
