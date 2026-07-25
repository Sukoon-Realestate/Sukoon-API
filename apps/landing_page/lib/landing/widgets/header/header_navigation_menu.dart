import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';

class HeaderNavigationMenu extends StatelessWidget {
  const HeaderNavigationMenu({
    required this.items,
    required this.onNavigate,
    super.key,
  });

  final List<(String, String)> items;
  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<String>(
      tooltip: LocaleKeys.landingOpenNavigation,
      onSelected: onNavigate,
      offset: const Offset(0, 48),
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: LandingColors.border),
      ),
      itemBuilder: (context) => items
          .map(
            (item) => PopupMenuItem<String>(
              value: item.$2,
              child: SizedBox(
                width: 210,
                child: Text(
                  item.$1,
                  textAlign: TextAlign.start,
                  style: const TextStyle(
                    color: LandingColors.navy,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          )
          .toList(),
      icon: const Icon(Icons.menu_rounded, color: LandingColors.navy),
    );
  }
}
