import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

import '../widgets/tenant_property_location/imports.dart';

class TenantPropertyLocationScreen extends StatelessWidget {
  const TenantPropertyLocationScreen({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TenantLocationTopBar(onBack: () => Navigator.of(context).pop()),
              Padding(
                padding: EdgeInsets.all(18.w),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Container(
                      height: 240.h,
                      clipBehavior: Clip.antiAlias,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(24.r),
                        gradient: const LinearGradient(
                          begin: AlignmentDirectional.topStart,
                          end: AlignmentDirectional.bottomEnd,
                          colors: [
                            Color(0xFFD1E8FF),
                            Color(0xFFC8E6C9),
                            Color(0xFFFFE0B2),
                          ],
                        ),
                      ),
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          Positioned.fill(
                            child: CustomPaint(painter: TenantMapGridPainter()),
                          ),
                          Container(
                            width: 82.r,
                            height: 82.r,
                            decoration: BoxDecoration(
                              color: AppColors.tealAlpha19,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: AppColors.sokoonTeal,
                                width: 1.5,
                              ),
                            ),
                          ),
                          Container(
                            width: 38.r,
                            height: 38.r,
                            decoration: const BoxDecoration(
                              color: AppColors.sokoonTeal,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              Icons.location_on_rounded,
                              color: AppColors.white,
                              size: 20.r,
                            ),
                          ),
                        ],
                      ),
                    ),
                    12.szH,
                    Container(
                      padding: EdgeInsets.all(12.w),
                      decoration: BoxDecoration(
                        color: AppColors.bluePale,
                        borderRadius: BorderRadius.circular(14.r),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.privacy_tip_outlined,
                            color: AppColors.blue,
                            size: 17.r,
                          ),
                          8.szW,
                          Expanded(
                            child: AppText(
                              'الموقع المعروض تقريبي لحماية خصوصية المالك',
                              color: AppColors.blue,
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                    16.szH,
                    Container(
                      padding: EdgeInsets.all(16.w),
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
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          AppText(
                            'قريب من',
                            color: AppColors.sokoonNavy,
                            fontSize: 15.sp,
                            fontWeight: FontWeight.w900,
                          ),
                          8.szH,
                          for (
                            int index = 0;
                            index < property.nearbyPlaces.length;
                            index++
                          ) ...[
                            TenantNearbyPlaceRow(
                              place: property.nearbyPlaces[index],
                            ),
                            if (index < property.nearbyPlaces.length - 1)
                              const Divider(color: AppColors.sokoonBorder),
                          ],
                        ],
                      ),
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
