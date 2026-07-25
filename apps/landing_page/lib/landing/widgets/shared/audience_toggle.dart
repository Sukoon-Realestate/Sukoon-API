import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';

class AudienceToggle extends StatelessWidget {
  const AudienceToggle({
    required this.value,
    required this.onChanged,
    super.key,
    this.compactLabels = false,
  });

  final Audience value;
  final ValueChanged<Audience> onChanged;
  final bool compactLabels;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final idealItemWidth = compactLabels ? 150.0 : 142.0;
        final availableWidth = constraints.maxWidth.isFinite
            ? constraints.maxWidth - 8
            : idealItemWidth * Audience.values.length;
        final itemWidth = math.min(
          idealItemWidth,
          availableWidth / Audience.values.length,
        );

        return Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: LandingColors.softSurface,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: Audience.values.map((audience) {
              final selected = audience == value;
              final color = audience == Audience.tenant
                  ? LandingColors.teal
                  : LandingColors.gold;
              final label = switch ((audience, compactLabels)) {
                (Audience.tenant, true) => LocaleKeys.landingAudienceTenant,
                (Audience.owner, true) => LocaleKeys.landingAudienceOwner,
                (Audience.tenant, false) => LocaleKeys.landingAudienceTenantTab,
                (Audience.owner, false) => LocaleKeys.landingAudienceOwnerTab,
              };
              final icon = audience == Audience.tenant
                  ? Icons.key_rounded
                  : Icons.home_rounded;
              return SizedBox(
                width: itemWidth,
                child: Semantics(
                  selected: selected,
                  button: true,
                  child: Material(
                    color: selected ? color : Colors.transparent,
                    borderRadius: BorderRadius.circular(12),
                    child: InkWell(
                      onTap: () => onChanged(audience),
                      borderRadius: BorderRadius.circular(12),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 180),
                        height: 44,
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        alignment: Alignment.center,
                        child: FittedBox(
                          fit: BoxFit.scaleDown,
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (!compactLabels) ...[
                                Icon(
                                  icon,
                                  color: selected
                                      ? Colors.white
                                      : LandingColors.subtext,
                                  size: 18,
                                ),
                                const SizedBox(width: 7),
                              ],
                              Text(
                                label,
                                style: TextStyle(
                                  color: selected
                                      ? Colors.white
                                      : LandingColors.subtext,
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        );
      },
    );
  }
}
