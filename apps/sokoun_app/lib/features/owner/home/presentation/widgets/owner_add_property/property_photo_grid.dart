import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'animated_property_photo_grid.dart';

export 'property_photo_tile.dart';

class PhotoGridSection extends StatelessWidget {
  const PhotoGridSection({
    super.key,
    required this.photos,
    required this.onAddPhotos,
    required this.onRemovePhoto,
    required this.onReplacePhoto,
    required this.onMainPhotoSelected,
  });

  final List<OwnerPropertyPhotoDraft> photos;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;
  final ValueChanged<int> onReplacePhoto;
  final ValueChanged<int> onMainPhotoSelected;

  @override
  Widget build(BuildContext context) {
    final bool hasEnoughPhotos = Validators.hasEnoughPropertyPhotos(
      photos.length,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 10.h,
      children: [
        AppText(
          '${LocaleKeys.ownerPropertiesPhotos} *',
          style: AppTextStyles.semiBold.copyWith(color: AppColors.sokoonNavy),
        ),
        AnimatedPropertyPhotoGrid(
          photos: photos,
          onAddPhotos: onAddPhotos,
          onRemovePhoto: onRemovePhoto,
          onReplacePhoto: onReplacePhoto,
          onMainPhotoSelected: onMainPhotoSelected,
        ),
        AppText(
          LocaleKeys.ownerAddPropertyPhotosCount
              .replaceAll('{count}', '${photos.length}')
              .replaceAll(
                '{minimum}',
                '${OwnerAddPropertyContent.minimumPhotoCount}',
              ),
          style: AppTextStyles.bold12.copyWith(
            color: hasEnoughPhotos ? AppColors.green : AppColors.sokoonGray,
            fontSize: 12.sp,
            height: 1.45,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
