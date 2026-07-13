import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class HomeCircleButton extends StatelessWidget {
  const HomeCircleButton({
    super.key,
    required this.icon,
    required this.iconColor,
    this.backgroundColor = AppColors.white,
    this.showBadge = false,
  });

  final IconData icon;
  final Color iconColor;
  final Color backgroundColor;
  final bool showBadge;

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          width: 36.r,
          height: 36.r,
          decoration: BoxDecoration(
            color: backgroundColor,
            shape: BoxShape.circle,
            border: Border.all(color: AppColors.sokoonBorder),
          ),
          child: Icon(icon, color: iconColor, size: 18.r),
        ),
        if (showBadge)
          PositionedDirectional(
            top: 2.r,
            end: 2.r,
            child: Container(
              width: 8.r,
              height: 8.r,
              decoration: const BoxDecoration(
                color: AppColors.red,
                shape: BoxShape.circle,
              ),
            ),
          ),
      ],
    );
  }
}

class HomeAvatar extends StatelessWidget {
  const HomeAvatar({
    super.key,
    required this.icon,
    required this.backgroundColor,
    required this.iconColor,
  });

  final IconData icon;
  final Color backgroundColor;
  final Color iconColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 36.r,
      height: 36.r,
      decoration: BoxDecoration(color: backgroundColor, shape: BoxShape.circle),
      child: Icon(icon, color: iconColor, size: 18.r),
    );
  }
}

class HomeSectionHeader extends StatelessWidget {
  const HomeSectionHeader({
    super.key,
    required this.title,
    this.actionTitle,
    this.onActionTap,
  });

  final String title;
  final String? actionTitle;
  final VoidCallback? onActionTap;

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.ltr,
      children: [
        if (actionTitle != null)
          TextButton(
            onPressed: onActionTap,
            style: TextButton.styleFrom(
              minimumSize: Size.zero,
              padding: EdgeInsets.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: AppText(
              actionTitle!,
              color: AppColors.sokoonTeal,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
            ),
          ),
        const Spacer(),
        AppText(
          title,
          color: AppColors.sokoonNavy,
          fontSize: 15.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.right,
        ),
      ],
    );
  }
}

class HomeSearchBox extends StatelessWidget {
  const HomeSearchBox({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52.h,
      padding: EdgeInsetsDirectional.only(start: 16.w, end: 8.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Icon(Icons.search_rounded, color: AppColors.sokoonMuted, size: 20.r),
          10.szW,
          Expanded(
            child: AppText(
              'ابحث عن منطقة أو حي…',
              color: AppColors.sokoonMuted,
              fontSize: 14.sp,
              fontWeight: FontWeight.w400,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Container(
            width: 34.r,
            height: 34.r,
            decoration: BoxDecoration(
              color: AppColors.sokoonTeal,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(Icons.tune_rounded, color: AppColors.white, size: 17.r),
          ),
        ],
      ),
    );
  }
}

class TenantVisitBanner extends StatelessWidget {
  const TenantVisitBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 13.h),
      decoration: BoxDecoration(
        color: AppColors.mintLight,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.tealAlpha19),
      ),
      child: Row(
        children: [
          Container(
            width: 34.r,
            height: 34.r,
            decoration: const BoxDecoration(
              color: AppColors.whiteAlpha60,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.calendar_today_outlined,
              color: AppColors.sokoonTeal,
              size: 17.r,
            ),
          ),
          12.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  'عندك زيارة النهارده 3:00 م',
                  color: AppColors.sokoonTeal,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  'شقة مدينة نصر',
                  color: AppColors.sokoonTeal,
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w500,
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_left_rounded, color: AppColors.sokoonTeal),
        ],
      ),
    );
  }
}

class TenantPropertyCard extends StatelessWidget {
  const TenantPropertyCard({
    super.key,
    required this.title,
    required this.rating,
    required this.area,
    required this.price,
    required this.icon,
  });

  final String title;
  final String rating;
  final String area;
  final String price;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 94.h,
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      clipBehavior: Clip.antiAlias,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Container(
            width: 96.w,
            height: double.infinity,
            color: AppColors.grayBluePale,
            child: Icon(icon, color: AppColors.blueGrayLight, size: 26.r),
          ),
          Expanded(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  AppText(
                    title,
                    color: AppColors.sokoonNavy,
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w900,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  6.szH,
                  Row(
                    children: [
                      Icon(
                        Icons.star_rounded,
                        color: AppColors.amber,
                        size: 14.r,
                      ),
                      3.szW,
                      AppText(
                        rating,
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                      ),
                      8.szW,
                      AppText(
                        '·',
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                      ),
                      8.szW,
                      AppText(
                        area,
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                      ),
                    ],
                  ),
                  const Spacer(),
                  Align(
                    alignment: AlignmentDirectional.centerEnd,
                    child: AppText(
                      price,
                      color: AppColors.sokoonTeal,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class OwnerStatCard extends StatelessWidget {
  const OwnerStatCard({
    super.key,
    required this.value,
    required this.label,
    required this.icon,
    required this.iconColor,
    required this.iconBackgroundColor,
  });

  final String value;
  final String label;
  final IconData icon;
  final Color iconColor;
  final Color iconBackgroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 118.h,
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34.r,
            height: 34.r,
            decoration: BoxDecoration(
              color: iconBackgroundColor,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(icon, color: iconColor, size: 18.r),
          ),
          const Spacer(),
          AppText(
            value,
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
          ),
          2.szH,
          AppText(
            label,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

class OwnerRequestCard extends StatelessWidget {
  const OwnerRequestCard({
    super.key,
    required this.name,
    required this.details,
  });

  final String name;
  final String details;

  @override
  Widget build(BuildContext context) {
    return Container(
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
        textDirection: TextDirection.ltr,
        children: [
          Container(
            width: 38.r,
            height: 38.r,
            decoration: const BoxDecoration(
              color: AppColors.bluePale,
              shape: BoxShape.circle,
            ),
            child: Icon(
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
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  details,
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w400,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          8.szW,
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              DefaultButton(
                onTap: () {},
                title: 'قبول',
                color: AppColors.emerald,
                textColor: AppColors.white,
                borderRadius: BorderRadius.circular(10.r),
                width: 45.w,
                height: 30.h,
                fontSize: 12.sp,
                fontWeight: FontWeight.w900,
              ),
              5.szW,
              DefaultButton(
                onTap: () {},
                title: 'رفض',
                color: AppColors.redPale,
                textColor: AppColors.red,
                borderRadius: BorderRadius.circular(10.r),
                width: 43.w,
                height: 30.h,
                fontSize: 12.sp,
                fontWeight: FontWeight.w900,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class HomeBottomNav extends StatelessWidget {
  const HomeBottomNav({super.key, required this.items});

  final List<HomeBottomNavItemData> items;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 70.h,
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: items.map((item) {
          return Expanded(child: _HomeBottomNavItem(item: item));
        }).toList(),
      ),
    );
  }
}

class HomeBottomNavItemData {
  const HomeBottomNavItemData({
    required this.icon,
    required this.label,
    this.isActive = false,
  });

  final IconData icon;
  final String label;
  final bool isActive;
}

class _HomeBottomNavItem extends StatelessWidget {
  const _HomeBottomNavItem({required this.item});

  final HomeBottomNavItemData item;

  @override
  Widget build(BuildContext context) {
    final color = item.isActive ? AppColors.sokoonTeal : AppColors.sokoonMuted;

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(item.icon, color: color, size: 22.r),
        3.szH,
        AppText(
          item.label,
          color: color,
          fontSize: 11.sp,
          fontWeight: FontWeight.w600,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
