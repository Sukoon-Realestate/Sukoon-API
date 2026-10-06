import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';

class SuggestedAreaCard extends StatelessWidget {
  const SuggestedAreaCard({
    super.key,
    required this.place,
    required this.styleIndex,
    this.isSelected = false,
    this.onTap,
  });

  static const List<Color> _backgroundColors = [
    AppColors.orangePale,
    AppColors.bluePale,
    AppColors.mintLight,
    AppColors.grayBackground,
    AppColors.redPale,
    AppColors.greenPale,
  ];
  static const List<Color> _iconColors = [
    AppColors.amber,
    AppColors.blue,
    AppColors.sokoonTeal,
    AppColors.sokoonGray,
    AppColors.red,
    AppColors.green,
  ];
  static const List<IconData> _icons = [
    Icons.location_city_outlined,
    Icons.maps_home_work_outlined,
    Icons.apartment_rounded,
    Icons.account_balance_outlined,
    Icons.park_outlined,
    Icons.location_on_outlined,
  ];

  final AvailablePlaceModel place;
  final int styleIndex;
  final bool isSelected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 86.h,
        padding: EdgeInsets.all(12.w),
        decoration: BoxDecoration(
          color: _backgroundColors[styleIndex % _backgroundColors.length],
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(
            color: isSelected
                ? context.appColor(AppColors.sokoonTeal)
                : AppColors.transparent,
            width: 1.4,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              _icons[styleIndex % _icons.length],
              color: _iconColors[styleIndex % _iconColors.length],
              size: 18.r,
            ),
            7.szH,
            AppText(
              place.district,
              style: AppTextStyles.bold12.copyWith(
                color: isSelected
                    ? context.appColor(AppColors.sokoonTeal)
                    : context.appColor(AppColors.sokoonNavy),
                fontSize: 12.sp,
                height: 1.45,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.start,
            ),
            3.szH,
            AppText(
              [
                place.city,
                place.country,
              ].where((value) => value.isNotEmpty).join('، '),
              style: AppTextStyles.semiBold.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 10.sp,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.start,
            ),
          ],
        ),
      ),
    );
  }
}
