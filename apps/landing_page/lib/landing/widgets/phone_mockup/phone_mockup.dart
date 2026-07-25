import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import 'owner_phone_preview.dart';
import 'phone_side_button.dart';
import 'tenant_phone_preview.dart';

class PhoneMockup extends StatelessWidget {
  const PhoneMockup({required this.audience, super.key, this.width = 202});

  final Audience audience;
  final double width;

  @override
  Widget build(BuildContext context) {
    final scale = width / 280;
    return Semantics(
      label: audience == Audience.tenant
          ? LocaleKeys.landingPhoneTenantSemantic
          : LocaleKeys.landingPhoneOwnerSemantic,
      image: true,
      child: SizedBox(
        width: width,
        height: 580 * scale,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xFF111113),
                  borderRadius: BorderRadius.circular(42 * scale),
                  border: Border.all(
                    color: const Color(0xFF3A3A3C),
                    width: 2 * scale,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.42),
                      offset: Offset(0, 24 * scale),
                      blurRadius: 55 * scale,
                    ),
                  ],
                ),
              ),
            ),
            Positioned(
              top: 14 * scale,
              left: (width - 70 * scale) / 2,
              width: 70 * scale,
              height: 9 * scale,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(9 * scale),
                ),
              ),
            ),
            Positioned(
              top: 28 * scale,
              left: 14 * scale,
              width: 252 * scale,
              height: 520 * scale,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(10 * scale),
                child: FittedBox(
                  fit: BoxFit.fill,
                  child: SizedBox(
                    width: 252,
                    height: 520,
                    child: audience == Audience.tenant
                        ? const TenantPhonePreview()
                        : const OwnerPhonePreview(),
                  ),
                ),
              ),
            ),
            Positioned(
              bottom: 10 * scale,
              left: (width - 64 * scale) / 2,
              width: 64 * scale,
              height: 4 * scale,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: const Color(0xFF3A3A3C),
                  borderRadius: BorderRadius.circular(4 * scale),
                ),
              ),
            ),
            PhoneSideButton(
              left: -2 * scale,
              top: 90 * scale,
              width: 3 * scale,
              height: 32 * scale,
            ),
            PhoneSideButton(
              left: -2 * scale,
              top: 132 * scale,
              width: 3 * scale,
              height: 46 * scale,
            ),
            PhoneSideButton(
              right: -2 * scale,
              top: 110 * scale,
              width: 3 * scale,
              height: 68 * scale,
            ),
          ],
        ),
      ),
    );
  }
}
