import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';

class OwnerRequestRow extends StatelessWidget {
  const OwnerRequestRow({required this.name, super.key});

  final String name;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        CircleAvatar(
          radius: 9,
          backgroundColor: LandingColors.tealLight,
          child: Text(
            name.characters.first,
            style: const TextStyle(
              color: LandingColors.teal,
              fontSize: 6,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        const SizedBox(width: 5),
        Expanded(
          child: Text(
            name,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: LandingColors.navy, fontSize: 7),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
          decoration: BoxDecoration(
            color: LandingColors.tealLight,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            LocaleKeys.landingPhoneNew,
            style: const TextStyle(
              color: LandingColors.teal,
              fontSize: 6,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }
}
