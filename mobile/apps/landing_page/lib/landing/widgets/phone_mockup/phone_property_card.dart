import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import '../shared/property_illustration.dart';

class PhonePropertyCard extends StatelessWidget {
  const PhonePropertyCard({
    required this.title,
    required this.area,
    required this.rooms,
    required this.price,
    required this.color,
    super.key,
  });

  final String title;
  final String area;
  final String rooms;
  final String price;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 152,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 7,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Stack(
              children: [
                Positioned.fill(child: PropertyIllustration(tint: color)),
                Positioned(
                  top: 7,
                  left: 7,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 7,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: LandingColors.teal,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.check, color: Colors.white, size: 7),
                        const SizedBox(width: 3),
                        Text(
                          LocaleKeys.landingVerified,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 7,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 6, 8, 7),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: LandingColors.navy,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  '$area · $rooms ${LocaleKeys.landingRooms}',
                  style: const TextStyle(
                    color: LandingColors.subtext,
                    fontSize: 7,
                  ),
                ),
                Text(
                  '$price ${LocaleKeys.landingPhoneCurrency}',
                  style: const TextStyle(
                    color: LandingColors.teal,
                    fontSize: 9.5,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
