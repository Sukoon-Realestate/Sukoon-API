import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';

class DetailsButton extends StatelessWidget {
  const DetailsButton({super.key, required this.propertyId});

  final String propertyId;

  void _openDetails() {
    if (propertyId.isEmpty) return;
    Go.to(PropertyDetailsScreen(propertyId: propertyId));
  }

  @override
  Widget build(BuildContext context) {
    return TextButton(
      onPressed: propertyId.isEmpty ? null : _openDetails,
      style: TextButton.styleFrom(
        minimumSize: const Size(48, 48),
        foregroundColor: context.appColor(AppColors.sokoonTeal),
      ),
      child: AppText(
        LocaleKeys.landingDetails,
        style: AppTextStyles.bold14.copyWith(
          color: context.appColor(AppColors.sokoonTeal),
        ),
      ),
    );
  }
}
