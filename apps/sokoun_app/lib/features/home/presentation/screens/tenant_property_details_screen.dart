import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';
import 'package:sokoun_app/features/visits/imports.dart';

import '../widgets/tenant_property_details/imports.dart';
import 'tenant_property_location_screen.dart';
import 'tenant_property_photos_screen.dart';

class TenantPropertyDetailsScreen extends StatefulWidget {
  const TenantPropertyDetailsScreen({super.key, this.item});

  final SearchResultContent? item;

  @override
  State<TenantPropertyDetailsScreen> createState() =>
      _TenantPropertyDetailsScreenState();
}

class _TenantPropertyDetailsScreenState
    extends State<TenantPropertyDetailsScreen> {
  late final TenantPropertyDetailsContent _property;
  bool _isSaved = false;

  @override
  void initState() {
    super.initState();
    _property = TenantPropertyDetailsContent.fromSearchResult(
      widget.item ?? TenantSearchResultContent.results.first,
    );
  }

  void _openPhotos([int index = 0]) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TenantPropertyPhotosScreen(
          property: _property,
          initialIndex: index,
        ),
      ),
    );
  }

  void _openLocation() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TenantPropertyLocationScreen(property: _property),
      ),
    );
  }

  void _openBookVisit() {
    Go.to(
      BookVisitScreen(
        property: VisitPropertyContent.fromPropertyDetails(_property),
      ),
    );
  }

  void _showShareSheet() {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.transparent,
      builder: (context) {
        return Directionality(
          textDirection: TextDirection.rtl,
          child: Container(
            padding: EdgeInsets.fromLTRB(20.w, 8.h, 20.w, 26.h),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
            ),
            child: SafeArea(
              top: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Center(
                    child: Container(
                      width: 42.w,
                      height: 4.h,
                      decoration: BoxDecoration(
                        color: AppColors.grayPale,
                        borderRadius: BorderRadius.circular(999.r),
                      ),
                    ),
                  ),
                  18.szH,
                  AppText(
                    'مشاركة العقار',
                    color: AppColors.sokoonNavy,
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w900,
                    textAlign: TextAlign.right,
                  ),
                  14.szH,
                  TenantPropertyShareActionRow(
                    icon: Icons.link_rounded,
                    label: 'نسخ الرابط',
                    color: AppColors.sokoonTeal,
                    onTap: () async {
                      await Clipboard.setData(
                        ClipboardData(text: _property.shareUrl),
                      );
                      if (context.mounted) {
                        Navigator.of(context).pop();
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('تم نسخ الرابط')),
                        );
                      }
                    },
                  ),
                  8.szH,
                  TenantPropertyShareActionRow(
                    icon: Icons.ios_share_rounded,
                    label: 'مشاركة',
                    color: AppColors.blue,
                    onTap: () => Navigator.of(context).pop(),
                  ),
                  8.szH,
                  TenantPropertyShareActionRow(
                    icon: Icons.close_rounded,
                    label: 'إلغاء',
                    color: AppColors.sokoonRose,
                    onTap: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          bottom: false,
          child: Column(
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      TenantPropertyHeroGallery(
                        property: _property,
                        isSaved: _isSaved,
                        onBack: () => Navigator.of(context).pop(),
                        onShare: _showShareSheet,
                        onSave: () => setState(() => _isSaved = !_isSaved),
                        onPhotosTap: _openPhotos,
                      ),
                      Padding(
                        padding: EdgeInsets.fromLTRB(18.w, 16.h, 18.w, 20.h),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            TenantPropertyTagRow(property: _property),
                            8.szH,
                            AppText(
                              _property.title,
                              color: AppColors.sokoonNavy,
                              fontSize: 19.sp,
                              fontWeight: FontWeight.w900,
                              textAlign: TextAlign.right,
                              maxLines: 2,
                            ),
                            8.szH,
                            GestureDetector(
                              onTap: _openLocation,
                              behavior: HitTestBehavior.opaque,
                              child: Row(
                                children: [
                                  Icon(
                                    Icons.location_on_outlined,
                                    color: AppColors.sokoonGray,
                                    size: 18.r,
                                  ),
                                  6.szW,
                                  Expanded(
                                    child: AppText(
                                      _property.location,
                                      color: AppColors.sokoonGray,
                                      fontSize: 13.sp,
                                      fontWeight: FontWeight.w500,
                                      textAlign: TextAlign.right,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            12.szH,
                            TenantPropertyPriceAndRating(property: _property),
                            14.szH,
                            TenantPropertyMetricsGrid(property: _property),
                            14.szH,
                            TenantPropertyInfoSection(
                              title: 'الوصف',
                              child: AppText(
                                _property.description,
                                color: AppColors.sokoonGray,
                                fontSize: 13.sp,
                                fontWeight: FontWeight.w500,
                                height: 1.45,
                                textAlign: TextAlign.right,
                              ),
                            ),
                            12.szH,
                            TenantPropertyInfoSection(
                              title: 'المرافق',
                              child: TenantPropertyAmenityWrap(
                                amenities: _property.amenities,
                              ),
                            ),
                            12.szH,
                            Container(
                              padding: EdgeInsets.all(14.w),
                              decoration: BoxDecoration(
                                color: AppColors.greenAlpha06,
                                borderRadius: BorderRadius.circular(14.r),
                                border: Border.all(
                                  color: AppColors.greenAlpha19,
                                ),
                              ),
                              child: Row(
                                children: [
                                  Icon(
                                    Icons.verified_user_outlined,
                                    color: AppColors.green,
                                    size: 18.r,
                                  ),
                                  8.szW,
                                  AppText(
                                    'تم التحقق من إثبات الملكية',
                                    color: AppColors.green,
                                    fontSize: 13.sp,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ],
                              ),
                            ),
                            12.szH,
                            Container(
                              padding: EdgeInsets.all(14.w),
                              decoration: BoxDecoration(
                                color: AppColors.amberPale,
                                borderRadius: BorderRadius.circular(12.r),
                                border: Border.all(
                                  color: AppColors.goldAlpha15,
                                ),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(
                                    Icons.info_outline_rounded,
                                    color: AppColors.brown,
                                    size: 18.r,
                                  ),
                                  8.szW,
                                  Expanded(
                                    child: AppText(
                                      'رسوم المنصة يتم خصمها من أرباح المالك — السعر المعروض هو ما ستدفعه فعلاً',
                                      color: AppColors.brown,
                                      fontSize: 12.sp,
                                      fontWeight: FontWeight.w500,
                                      maxLines: 2,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            12.szH,
                            TenantPropertyOwnerCard(property: _property),
                            28.szH,
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Container(
                padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 18.h),
                decoration: const BoxDecoration(
                  color: AppColors.white,
                  border: Border(top: BorderSide(color: AppColors.grayPale)),
                ),
                child: Row(
                  textDirection: TextDirection.ltr,
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: _openBookVisit,
                        behavior: HitTestBehavior.opaque,
                        child: Container(
                          height: 48.h,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: AppColors.sokoonTeal,
                            borderRadius: BorderRadius.circular(14.r),
                          ),
                          child: AppText(
                            'احجز زيارة',
                            color: AppColors.white,
                            fontSize: 15.sp,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                    ),
                    10.szW,
                    GestureDetector(
                      onTap: () => setState(() => _isSaved = !_isSaved),
                      behavior: HitTestBehavior.opaque,
                      child: Container(
                        width: 48.r,
                        height: 48.r,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: AppColors.grayBackground,
                          borderRadius: BorderRadius.circular(14.r),
                        ),
                        child: Icon(
                          _isSaved
                              ? Icons.bookmark_rounded
                              : Icons.bookmark_border_rounded,
                          color: AppColors.sokoonTeal,
                          size: 22.r,
                        ),
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
