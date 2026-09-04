import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import '../widgets/tenant_property_photos/imports.dart';

class TenantPropertyPhotosScreen extends StatefulWidget {
  const TenantPropertyPhotosScreen({
    super.key,
    required this.property,
    this.initialIndex = 2,
  });

  final TenantPropertyDetailsContent property;
  final int initialIndex;

  @override
  State<TenantPropertyPhotosScreen> createState() =>
      _TenantPropertyPhotosScreenState();
}

class _TenantPropertyPhotosScreenState
    extends State<TenantPropertyPhotosScreen> {
  late int _selectedIndex;

  @override
  void initState() {
    super.initState();
    _selectedIndex = widget.initialIndex
        .clamp(0, widget.property.photoLabels.length - 1)
        .toInt();
  }

  void _move(int delta) {
    final next = (_selectedIndex + delta)
        .clamp(0, widget.property.photoLabels.length - 1)
        .toInt();
    setState(() => _selectedIndex = next);
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.slate,
        body: SafeArea(
          child: Column(
            children: [
              Row(
                textDirection: TextDirection.ltr,
                children: [
                  TenantPhotoCircleIconButton(
                    icon: Icons.favorite_border_rounded,
                    onTap: () {},
                  ),
                  8.szW,
                  TenantPhotoCircleIconButton(
                    icon: Icons.share_outlined,
                    onTap: () {},
                  ),
                  const Spacer(),
                  TenantPhotoCircleIconButton(
                    icon: Icons.close_rounded,
                    onTap: Go.back,
                  ),
                ],
              ).paddingSymmetric(horizontal: 16.w, vertical: 10.h),
              Expanded(
                child: Container(
                  height: 280.h,
                  margin: EdgeInsets.symmetric(horizontal: 18.w),
                  decoration: BoxDecoration(
                    color: AppColors.slateDark,
                    borderRadius: BorderRadius.circular(24.r),
                  ),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      if (widget.property.imageUrls.isNotEmpty)
                        Positioned.fill(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(24.r),
                            child: CachedImage(
                              url:
                                  widget.property.imageUrls[_selectedIndex
                                      .clamp(
                                        0,
                                        widget.property.imageUrls.length - 1,
                                      )
                                      .toInt()],
                              fit: BoxFit.cover,
                              height: 280.h,
                            ),
                          ),
                        )
                      else
                        Icon(
                          Icons.apartment_outlined,
                          color: AppColors.whiteAlpha40,
                          size: 58.r,
                        ),
                      PositionedDirectional(
                        start: 12.w,
                        child: TenantPhotoNavButton(
                          icon: Icons.chevron_right_rounded,
                          onTap: () => _move(-1),
                        ),
                      ),
                      PositionedDirectional(
                        end: 12.w,
                        child: TenantPhotoNavButton(
                          icon: Icons.chevron_left_rounded,
                          onTap: () => _move(1),
                        ),
                      ),
                    ],
                  ),
                ).centerWidget,
              ),
              Column(
                children: [
                  AppText(
                    '${_selectedIndex + 1} / ${widget.property.photoLabels.length} — ${widget.property.photoLabels[_selectedIndex]}',
                    color: AppColors.white,
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w900,
                    textAlign: TextAlign.center,
                  ),
                  14.szH,
                  SizedBox(
                    height: 40.h,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      reverse: true,
                      itemBuilder: (context, index) {
                        final isSelected = index == _selectedIndex;
                        return GestureDetector(
                          onTap: () => setState(() => _selectedIndex = index),
                          behavior: HitTestBehavior.opaque,
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 180),
                            width: isSelected ? 42.w : 34.w,
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? AppColors.sokoonTeal
                                  : AppColors.slateGray,
                              borderRadius: BorderRadius.circular(12.r),
                              border: isSelected
                                  ? Border.all(color: AppColors.white)
                                  : null,
                            ),
                            child: Icon(
                              Icons.image_outlined,
                              color: AppColors.whiteAlpha60,
                              size: 16.r,
                            ),
                          ),
                        );
                      },
                      separatorBuilder: (context, index) => 8.szW,
                      itemCount: widget.property.photoLabels.length,
                    ),
                  ),
                ],
              ).paddingSymmetric(horizontal: 18.w, vertical: 16.h),
            ],
          ),
        ),
      ),
    );
  }
}
