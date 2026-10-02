import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class PropertyLocationControls extends StatelessWidget {
  const PropertyLocationControls({
    super.key,
    required this.satellite,
    required this.busy,
    required this.onLocate,
    required this.onToggleSatellite,
  });
  final bool satellite;
  final bool busy;
  final VoidCallback onLocate;
  final VoidCallback onToggleSatellite;

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8.w,
    children: [
      TextButton.icon(
        onPressed: busy ? null : onLocate,
        icon: const Icon(Icons.my_location_rounded),
        label: AppText(LocaleKeys.useMyLocation),
      ),
      TextButton.icon(
        onPressed: onToggleSatellite,
        icon: Icon(
          satellite ? Icons.map_outlined : Icons.satellite_alt_rounded,
        ),
        label: AppText(
          satellite
              ? LocaleKeys.propertyMapStandard
              : LocaleKeys.propertyMapSatellite,
        ),
      ),
    ],
  );
}
