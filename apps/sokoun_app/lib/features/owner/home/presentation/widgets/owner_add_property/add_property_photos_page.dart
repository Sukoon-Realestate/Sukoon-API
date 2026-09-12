import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyPhotosPage extends StatelessWidget {
  const AddPropertyPhotosPage({
    super.key,
    this.existingPhotoUrls = const [],
    required this.photos,
    required this.isReady,
    required this.onAddPhotos,
    required this.onRemovePhoto,
    required this.onNext,
    required this.onBack,
  });

  final List<String> existingPhotoUrls;
  final List<File> photos;
  final bool isReady;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;
  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    final int photoCount = existingPhotoUrls.length + photos.length;
    final int remaining =
        OwnerAddPropertyContent.minimumPhotoCount - photoCount;

    return AddPropertyStepShell(
      title: 'صور العقار',
      activeSegments: 2,
      segmentCount: 5,
      progressSubtitle: 'الخطوة 2 من 5 — صور العقار',
      primaryLabel: 'التالي — فيديو العقار',
      onPrimaryTap: isReady ? onNext : null,
      onBack: onBack,
      children: [
        AddPropertyInfoBanner(
          title: isReady ? 'الصور جاهزة للمراجعة' : null,
          text: isReady
              ? 'تقدر تضيف صور زيادة أو تكمل لخطوة الفيديو'
              : 'اضغط على مربعات الإضافة لرفع $remaining صور كمان',
          backgroundColor: isReady ? AppColors.greenPale : AppColors.orangePale,
          borderColor: isReady ? AppColors.greenAlpha19 : AppColors.goldAlpha15,
          iconColor: isReady ? AppColors.green : AppColors.brown,
          textColor: isReady ? AppColors.sokoonNavy : AppColors.brown,
          icon: isReady
              ? Icons.check_circle_outline_rounded
              : Icons.warning_amber_rounded,
        ),
        _PhotoGridSection(
          existingPhotoUrls: existingPhotoUrls,
          photos: photos,
          onAddPhotos: onAddPhotos,
          onRemovePhoto: onRemovePhoto,
        ),
        const _PhotoTipsSection(),
      ],
    );
  }
}

class _PhotoGridSection extends StatelessWidget {
  const _PhotoGridSection({
    required this.existingPhotoUrls,
    required this.photos,
    required this.onAddPhotos,
    required this.onRemovePhoto,
  });

  final List<String> existingPhotoUrls;
  final List<File> photos;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;

  @override
  Widget build(BuildContext context) {
    final int photoCount = existingPhotoUrls.length + photos.length;
    final bool isReady =
        photoCount >= OwnerAddPropertyContent.minimumPhotoCount;

    return Column(
      children: [
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            crossAxisSpacing: 10.w,
            mainAxisSpacing: 10.h,
            childAspectRatio: 1,
          ),
          itemCount: OwnerAddPropertyContent.maxPhotoCount,
          itemBuilder: (context, index) {
            final bool hasExistingPhoto = index < existingPhotoUrls.length;
            final int localPhotoIndex = index - existingPhotoUrls.length;
            final bool hasLocalPhoto =
                localPhotoIndex >= 0 && localPhotoIndex < photos.length;
            return _PhotoTile(
              imageUrl: hasExistingPhoto ? existingPhotoUrls[index] : null,
              photo: hasLocalPhoto ? photos[localPhotoIndex] : null,
              onAddPhotos: onAddPhotos,
              onRemovePhoto: () => onRemovePhoto(index),
            );
          },
        ),
        10.szH,
        AppText(
          '$photoCount / ${OwnerAddPropertyContent.minimumPhotoCount} صور مرفوعة (الحد الأدنى ${OwnerAddPropertyContent.minimumPhotoCount})',
          color: isReady ? AppColors.green : AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w700,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _PhotoTile extends StatelessWidget {
  const _PhotoTile({
    required this.imageUrl,
    required this.photo,
    required this.onAddPhotos,
    required this.onRemovePhoto,
  });

  final String? imageUrl;
  final File? photo;
  final VoidCallback onAddPhotos;
  final VoidCallback onRemovePhoto;

  @override
  Widget build(BuildContext context) {
    final bool hasPhoto = photo != null || imageUrl != null;
    return GestureDetector(
      onTap: hasPhoto ? null : onAddPhotos,
      behavior: HitTestBehavior.opaque,
      child: Container(
        decoration: BoxDecoration(
          color: hasPhoto
              ? AppColors.grayBluePale
              : AppColors.scaffoldBackground,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(
            color: hasPhoto ? AppColors.transparent : AppColors.sokoonBorder,
            style: BorderStyle.solid,
          ),
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: hasPhoto
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(14.r),
                      child: photo != null
                          ? Image.file(photo!, fit: BoxFit.cover)
                          : Image.network(
                              imageUrl!,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) =>
                                  Icon(
                                    Icons.broken_image_outlined,
                                    color: AppColors.sokoonMuted,
                                    size: 24.r,
                                  ),
                            ),
                    )
                  : Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.add_rounded,
                          color: AppColors.sokoonMuted,
                          size: 20.r,
                        ),
                        4.szH,
                        AppText(
                          'إضافة',
                          color: AppColors.sokoonMuted,
                          fontSize: 10.sp,
                          fontWeight: FontWeight.w600,
                        ),
                      ],
                    ).centerWidget,
            ),
            if (hasPhoto)
              PositionedDirectional(
                top: 6.r,
                start: 6.r,
                child: GestureDetector(
                  onTap: onRemovePhoto,
                  behavior: HitTestBehavior.opaque,
                  child: Container(
                    width: 20.r,
                    height: 20.r,
                    alignment: Alignment.center,
                    decoration: const BoxDecoration(
                      color: AppColors.red,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.close_rounded,
                      color: AppColors.white,
                      size: 12.r,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _PhotoTipsSection extends StatelessWidget {
  const _PhotoTipsSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'نصائح للصور',
      child: Column(
        children: [
          for (
            int index = 0;
            index < OwnerAddPropertyContent.photoTips.length;
            index++
          ) ...[
            _TipRow(text: OwnerAddPropertyContent.photoTips[index]),
            if (index < OwnerAddPropertyContent.photoTips.length - 1)
              const Divider(color: AppColors.sokoonBorder),
          ],
        ],
      ),
    );
  }
}

class _TipRow extends StatelessWidget {
  const _TipRow({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          Icons.check_circle_outline_rounded,
          color: AppColors.sokoonTeal,
          size: 16.r,
        ),
        8.szW,
        Expanded(
          child: AppText(
            text,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    ).paddingSymmetric(vertical: 4.h);
  }
}
