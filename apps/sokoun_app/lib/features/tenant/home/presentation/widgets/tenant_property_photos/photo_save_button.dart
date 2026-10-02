import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';

import '../../../data/property_photo_gallery_data.dart';
import '../../cubits/property_photo_save_cubit.dart';

class TenantPropertyPhotoSaveButton extends StatelessWidget {
  const TenantPropertyPhotoSaveButton({super.key, required this.imageUrl});

  final String imageUrl;

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<PropertyPhotoSaveCubit, PropertyPhotoSaveState>(
      listenWhen: (previous, current) => previous.status != current.status,
      listener: (context, state) {
        if (state.status.isSuccess) {
          Messages.showToast(
            msg: LocaleKeys.tenantPropertyPhotoSaved.replaceAll(
              '@album',
              PropertyPhotoGalleryData.albumName,
            ),
          );
        } else if (state.status.isError) {
          Messages.showToast(
            msg: state.errorMessage ?? LocaleKeys.tenantPropertyPhotoSaveFailed,
            status: BaseStatus.error,
          );
        }
      },
      builder: (context, state) {
        final bool isSaving = state.status.isLoading;
        return SizedBox.square(
          dimension: 48.r,
          child: IconButton(
            tooltip: isSaving
                ? LocaleKeys.tenantPropertyPhotoSaving
                : LocaleKeys.tenantPropertyPhotoSave,
            onPressed: isSaving
                ? null
                : () => context.read<PropertyPhotoSaveCubit>().saveImage(
                    imageUrl,
                  ),
            style: IconButton.styleFrom(
              backgroundColor: AppColors.blackAlpha35,
              disabledBackgroundColor: AppColors.blackAlpha35,
              foregroundColor: AppColors.white,
              padding: EdgeInsets.zero,
              shape: const CircleBorder(),
            ),
            icon: isSaving
                ? SizedBox.square(
                    dimension: 18.r,
                    child: CircularProgressIndicator(
                      value: state.progress,
                      strokeWidth: 2,
                      color: AppColors.white,
                    ),
                  )
                : Icon(Icons.download_rounded, size: 18.r),
          ),
        );
      },
    );
  }
}
