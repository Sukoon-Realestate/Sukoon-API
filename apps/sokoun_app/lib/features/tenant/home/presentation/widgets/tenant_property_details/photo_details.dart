import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart';

import 'info_section.dart';

class TenantPropertyPhotoDetails extends StatelessWidget {
  const TenantPropertyPhotoDetails({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) => TenantPropertyInfoSection(
    title: LocaleKeys.ownerPropertiesPhotos,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (int index = 0; index < property.imageUrls.length; index++)
          Material(
            type: MaterialType.transparency,
            child: ListTile(
              contentPadding: EdgeInsets.zero,
              title: AppText(
                index < property.photoLabels.length
                    ? property.photoLabels[index]
                    : LocaleKeys.ownerAddPropertyPhotoNumber.replaceAll(
                        '{number}',
                        '${index + 1}',
                      ),
              ),
              subtitle:
                  index < property.photoDescriptions.length &&
                      property.photoDescriptions[index].trim().isNotEmpty
                  ? AppText(property.photoDescriptions[index])
                  : null,
              trailing: Icon(
                Directionality.of(context) == TextDirection.rtl
                    ? Icons.chevron_left_rounded
                    : Icons.chevron_right_rounded,
              ),
              onTap: () => Go.to(
                TenantPropertyPhotosScreen(
                  property: property,
                  initialIndex: index,
                ),
              ),
            ),
          ),
      ],
    ),
  );
}
