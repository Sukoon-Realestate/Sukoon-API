import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import '../../../data/models/property_location.dart';
import '../../screens/property_location_picker_screen.dart';
import 'add_property_section_card.dart';
import 'add_property_info_banner.dart';
import 'add_property_primary_button.dart';

class AddPropertyMapSection extends StatefulWidget {
  const AddPropertyMapSection({
    super.key,
    required this.location,
    required this.query,
    required this.onLocationSelected,
  });
  final PropertyLocation? location;
  final String query;
  final ValueChanged<PropertyLocation> onLocationSelected;

  @override
  State<AddPropertyMapSection> createState() => _AddPropertyMapSectionState();
}

class _AddPropertyMapSectionState extends State<AddPropertyMapSection> {
  bool _isOpen = false;
  Future<void> _pick() async {
    if (_isOpen) return;
    _isOpen = true;
    FocusManager.instance.primaryFocus?.unfocus();
    try {
      final location = await Go.to<PropertyLocation>(
        PropertyLocationPickerScreen(
          initialLocation: widget.location,
          initialQuery: widget.query,
        ),
      );
      if (mounted && location != null) widget.onLocationSelected(location);
    } finally {
      _isOpen = false;
    }
  }

  @override
  Widget build(BuildContext context) => AddPropertySectionCard(
    title: LocaleKeys.ownerAddPropertyMapTitle,
    subtitle: LocaleKeys.propertyMapTapHint,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12.h,
      children: [
        if (widget.location case final location?) ...[
          AddPropertyInfoBanner(
            title: LocaleKeys.ownerAddPropertySelectedLocation,
            text: location.address.isEmpty ? widget.query : location.address,
            backgroundColor: context.appColor(
              AppColors.greenPale,
              surface: true,
            ),
            borderColor: AppColors.greenAlpha19,
            iconColor: context.appColor(AppColors.green),
            icon: Icons.location_on_outlined,
          ),
          Text(location.coordinates, textDirection: TextDirection.ltr),
        ],
        AddPropertyPrimaryButton(
          label: widget.location == null
              ? LocaleKeys.ownerAddPropertySelectLocation
              : LocaleKeys.propertyMapChange,
          onTap: _pick,
        ),
      ],
    ),
  );
}
