import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import '../cubits/property_photo_save_cubit.dart';
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
  late final ValueNotifier<int> _selectedIndex;

  @override
  void initState() {
    super.initState();
    _selectedIndex = ValueNotifier<int>(
      widget.initialIndex
          .clamp(0, widget.property.photoLabels.length - 1)
          .toInt(),
    );
  }

  @override
  void dispose() {
    _selectedIndex.dispose();
    super.dispose();
  }

  void _move(int delta) {
    final int next = (_selectedIndex.value + delta)
        .clamp(0, widget.property.photoLabels.length - 1)
        .toInt();
    _selectedIndex.value = next;
  }

  @override
  Widget build(BuildContext context) {
    final List<String> imageUrls = widget.property.imageUrls;
    return Scaffold(
      backgroundColor: AppColors.slate,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TenantPhotoCircleIconButton(
              icon: Icons.close_rounded,
              onTap: Go.back,
            ).paddingAll(20.r),
            Expanded(
              child: ValueListenableBuilder<int>(
                valueListenable: _selectedIndex,
                builder: (context, selectedIndex, _) => Container(
                  height: 280.h,
                  margin: EdgeInsets.symmetric(horizontal: 18.w),
                  decoration: BoxDecoration(
                    color: AppColors.slateDark,
                    borderRadius: BorderRadius.circular(24.r),
                  ),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      if (imageUrls.isNotEmpty)
                        Positioned.fill(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(24.r),
                            child: CachedImage(
                              url:
                                  imageUrls[selectedIndex
                                      .clamp(0, imageUrls.length - 1)
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
                      if (imageUrls.isNotEmpty)
                        PositionedDirectional(
                          top: 12.h,
                          end: 12.w,
                          child: BlocProvider(
                            create: (_) => PropertyPhotoSaveCubit(),
                            child: TenantPropertyPhotoSaveButton(
                              imageUrl:
                                  imageUrls[selectedIndex
                                      .clamp(0, imageUrls.length - 1)
                                      .toInt()],
                            ),
                          ),
                        ),
                      PositionedDirectional(
                        start: 12.w,
                        child: TenantPhotoNavButton(
                          icon: Icons.chevron_left_rounded,
                          onTap: () => _move(-1),
                        ),
                      ),
                      PositionedDirectional(
                        end: 12.w,
                        child: TenantPhotoNavButton(
                          icon: Icons.chevron_right_rounded,
                          onTap: () => _move(1),
                        ),
                      ),
                    ],
                  ),
                ).centerWidget,
              ),
            ),
            ValueListenableBuilder<int>(
              valueListenable: _selectedIndex,
              builder: (context, selectedIndex, _) => Column(
                spacing: 14.h,
                children: [
                  AppText(
                    '${selectedIndex + 1} / ${widget.property.photoLabels.length} — ${widget.property.photoLabels[selectedIndex]}',
                    style: AppTextStyles.bold14.copyWith(
                      color: AppColors.white,
                      fontSize: 14.sp,
                      height: 1.45,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  SizedBox(
                    height: 40.h,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      reverse: true,
                      itemBuilder: (context, index) {
                        final bool isSelected = index == selectedIndex;
                        return GestureDetector(
                          onTap: () => _selectedIndex.value = index,
                          behavior: HitTestBehavior.opaque,
                          child: AnimatedContainer(
                            duration: SokounMotion.duration(
                              context,
                              milliseconds: 180,
                            ),
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
            ),
          ],
        ),
      ),
    );
  }
}
