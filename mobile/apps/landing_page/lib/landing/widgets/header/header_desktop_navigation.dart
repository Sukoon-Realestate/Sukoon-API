import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';

class HeaderDesktopNavigation extends StatelessWidget {
  const HeaderDesktopNavigation({
    required this.items,
    required this.onNavigate,
    super.key,
  });

  final List<(String, String)> items;
  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: FittedBox(
        fit: BoxFit.scaleDown,
        child: Row(
          children: items
              .map(
                (item) => Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: TextButton(
                    onPressed: () => onNavigate(item.$2),
                    style: TextButton.styleFrom(
                      foregroundColor: LandingColors.navy,
                      padding: const EdgeInsets.symmetric(horizontal: 5),
                    ),
                    child: Text(
                      item.$1,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              )
              .toList(),
        ),
      ),
    );
  }
}
