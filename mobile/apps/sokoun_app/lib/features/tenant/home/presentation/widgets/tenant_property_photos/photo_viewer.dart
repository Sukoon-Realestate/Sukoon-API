import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/image_widgets/cached_image.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import 'photo_caption.dart';
import 'photo_nav_button.dart';
import 'photo_save_button.dart';

class TenantPropertyPhotoViewer extends StatefulWidget {
  const TenantPropertyPhotoViewer({
    super.key,
    required this.property,
    this.initialIndex = 0,
  });

  final TenantPropertyDetailsContent property;
  final int initialIndex;

  @override
  State<TenantPropertyPhotoViewer> createState() =>
      _TenantPropertyPhotoViewerState();
}

class _TenantPropertyPhotoViewerState extends State<TenantPropertyPhotoViewer> {
  late final ValueNotifier<int> _selectedIndex;

  int _clamp(int index) => widget.property.imageUrls.isEmpty
      ? 0
      : index.clamp(0, widget.property.imageUrls.length - 1);

  @override
  void initState() {
    super.initState();
    _selectedIndex = ValueNotifier(_clamp(widget.initialIndex));
  }

  @override
  void didUpdateWidget(covariant TenantPropertyPhotoViewer oldWidget) {
    super.didUpdateWidget(oldWidget);
    _selectedIndex.value = _clamp(
      oldWidget.property.id != widget.property.id
          ? widget.initialIndex
          : _selectedIndex.value,
    );
  }

  @override
  void dispose() {
    _selectedIndex.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final List<String> urls = widget.property.imageUrls;
    if (urls.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: 12.h,
          children: [
            Icon(
              Icons.apartment_outlined,
              color: AppColors.whiteAlpha60,
              size: 48.r,
            ),
            AppText(
              LocaleKeys.tenantPropertyPhotosEmpty,
              color: AppColors.white,
            ),
          ],
        ),
      );
    }
    final bool rtl = Directionality.of(context) == TextDirection.rtl;
    return LayoutBuilder(
      builder: (context, constraints) => ValueListenableBuilder<int>(
        valueListenable: _selectedIndex,
        builder: (context, index, _) {
          final String name = index < widget.property.photoLabels.length
              ? widget.property.photoLabels[index]
              : '${LocaleKeys.tenantPropertyDetailsPhotoCountUnit} ${index + 1}';
          final String description =
              index < widget.property.photoDescriptions.length
              ? widget.property.photoDescriptions[index]
              : '';
          return Column(
            children: [
              Expanded(
                child: Container(
                  margin: EdgeInsets.symmetric(horizontal: 18.w),
                  decoration: BoxDecoration(
                    color: AppColors.slateDark,
                    borderRadius: BorderRadius.circular(20.r),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      Positioned.fill(
                        child: Semantics(
                          label: name,
                          image: true,
                          child: CachedImage(
                            url: urls[index],
                            fit: BoxFit.contain,
                            bgColor: AppColors.slateDark,
                          ),
                        ),
                      ),
                      PositionedDirectional(
                        top: 12.h,
                        end: 12.w,
                        child: TenantPropertyPhotoSaveButton(
                          imageUrl: urls[index],
                        ),
                      ),
                      PositionedDirectional(
                        start: 8.w,
                        child: TenantPhotoNavButton(
                          icon: rtl
                              ? Icons.chevron_right_rounded
                              : Icons.chevron_left_rounded,
                          tooltip: LocaleKeys.tenantPropertyPhotosPrevious,
                          onTap: index > 0
                              ? () => _selectedIndex.value = index - 1
                              : null,
                        ),
                      ),
                      PositionedDirectional(
                        end: 8.w,
                        child: TenantPhotoNavButton(
                          icon: rtl
                              ? Icons.chevron_left_rounded
                              : Icons.chevron_right_rounded,
                          tooltip: LocaleKeys.tenantPropertyPhotosNext,
                          onTap: index < urls.length - 1
                              ? () => _selectedIndex.value = index + 1
                              : null,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: constraints.maxHeight * .4,
                ),
                child: SingleChildScrollView(
                  child: TenantPropertyPhotoCaption(
                    name: name,
                    description: description,
                    index: index,
                    total: urls.length,
                  ).paddingSymmetric(horizontal: 18.w, vertical: 16.h),
                ),
              ),
              SizedBox(
                height: 56.h,
                child: ListView.separated(
                  padding: EdgeInsets.symmetric(horizontal: 18.w),
                  scrollDirection: Axis.horizontal,
                  itemCount: urls.length,
                  separatorBuilder: (context, index) => 8.szW,
                  itemBuilder: (context, photoIndex) => Semantics(
                    button: true,
                    selected: photoIndex == index,
                    label: '${photoIndex + 1} / ${urls.length}',
                    child: Material(
                      color: context.appColor(
                        AppColors.slateGray,
                        surface: true,
                      ),
                      borderRadius: BorderRadius.circular(10.r),
                      clipBehavior: Clip.antiAlias,
                      child: InkWell(
                        onTap: () => _selectedIndex.value = photoIndex,
                        child: Container(
                          width: 56.w,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(10.r),
                            border: Border.all(
                              color: photoIndex == index
                                  ? AppColors.white
                                  : AppColors.transparent,
                              width: 2,
                            ),
                          ),
                          child: CachedImage(
                            url: urls[photoIndex],
                            fit: BoxFit.cover,
                            width: 56.w,
                            height: 56.h,
                            bgColor: context.appColor(AppColors.slateGray),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              16.szH,
            ],
          );
        },
      ),
    );
  }
}
