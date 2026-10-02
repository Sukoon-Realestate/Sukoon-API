import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../shared/property_illustration.dart';

class PropertyCardMedia extends StatelessWidget {
  const PropertyCardMedia({
    required this.property,
    required this.isSaved,
    required this.onFavoriteToggle,
    super.key,
  });

  final PropertyItem property;
  final bool isSaved;
  final VoidCallback onFavoriteToggle;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 180,
      child: Stack(
        children: [
          Positioned.fill(
            child: PropertyIllustration(tint: property.imageColor),
          ),
          if (property.isVerified)
            Positioned(
              top: 12,
              right: 12,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: LandingColors.teal,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.check_rounded,
                      color: Colors.white,
                      size: 12,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      LocaleKeys.landingVerified,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          Positioned(
            top: 10,
            left: 10,
            child: Material(
              color: Colors.white.withValues(alpha: 0.93),
              shape: const CircleBorder(),
              child: IconButton(
                tooltip: isSaved
                    ? LocaleKeys.landingRemoveFavorite
                    : LocaleKeys.landingAddFavorite,
                onPressed: onFavoriteToggle,
                icon: Icon(
                  isSaved
                      ? Icons.favorite_rounded
                      : Icons.favorite_border_rounded,
                  size: 19,
                  color: isSaved ? LandingColors.rose : const Color(0xFF9CA3AF),
                ),
              ),
            ),
          ),
          Positioned(
            bottom: 10,
            right: 12,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: LandingColors.teal.withValues(alpha: 0.08),
                border: Border.all(
                  color: LandingColors.teal.withValues(alpha: 0.18),
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                property.type,
                style: const TextStyle(
                  color: LandingColors.teal,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
