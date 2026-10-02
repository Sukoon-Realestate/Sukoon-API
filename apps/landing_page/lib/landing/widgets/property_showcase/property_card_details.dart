import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import '../shared/landing_button.dart';

class PropertyCardDetails extends StatelessWidget {
  const PropertyCardDetails({
    required this.property,
    required this.onDetails,
    super.key,
  });

  final PropertyItem property;
  final VoidCallback onDetails;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            property.title,
            style: const TextStyle(
              color: LandingColors.navy,
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              const Icon(
                Icons.location_on_outlined,
                size: 15,
                color: LandingColors.subtext,
              ),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  property.area,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: LandingColors.subtext,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 14,
            runSpacing: 8,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.home_outlined,
                    size: 15,
                    color: LandingColors.subtext,
                  ),
                  const SizedBox(width: 5),
                  Text(
                    '${property.rooms} ${LocaleKeys.landingRooms}',
                    style: const TextStyle(
                      color: LandingColors.subtext,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.crop_square_rounded,
                    size: 14,
                    color: LandingColors.subtext,
                  ),
                  const SizedBox(width: 5),
                  Text(
                    '${property.squareMeters} ${LocaleKeys.landingSquareMeters}',
                    style: const TextStyle(
                      color: LandingColors.subtext,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: RichText(
                  text: TextSpan(
                    style: DefaultTextStyle.of(context).style,
                    children: [
                      TextSpan(
                        text: property.price,
                        style: const TextStyle(
                          color: LandingColors.teal,
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      TextSpan(
                        text: ' ${LocaleKeys.landingPriceUnit}',
                        style: const TextStyle(
                          color: LandingColors.subtext,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              LandingButton(
                label: LocaleKeys.landingAppTag,
                onPressed: onDetails,
                height: 36,
                horizontalPadding: 16,
                radius: 10,
              ),
            ],
          ),
        ],
      ),
    );
  }
}
