import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

import '../cubits/property_photo_save_cubit.dart';
import '../widgets/tenant_property_photos/circle_icon_button.dart';
import '../widgets/tenant_property_photos/photo_viewer.dart';

class TenantPropertyPhotosScreen extends StatelessWidget {
  const TenantPropertyPhotosScreen({
    super.key,
    required this.property,
    this.initialIndex = 0,
  });

  final TenantPropertyDetailsContent property;
  final int initialIndex;

  @override
  Widget build(BuildContext context) => BlocProvider(
    create: (_) => PropertyPhotoSaveCubit(),
    child: Scaffold(
      backgroundColor: AppColors.slate,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TenantPhotoCircleIconButton(
              icon: Icons.close_rounded,
              tooltip: LocaleKeys.tenantPropertyPhotosClose,
              onTap: Go.back,
            ).paddingAll(16.r),
            Expanded(
              child: TenantPropertyPhotoViewer(
                property: property,
                initialIndex: initialIndex,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
