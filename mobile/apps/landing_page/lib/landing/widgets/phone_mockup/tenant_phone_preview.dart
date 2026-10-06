import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import 'phone_property_card.dart';
import 'phone_status_bar.dart';

class TenantPhonePreview extends StatelessWidget {
  const TenantPhonePreview({super.key});

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: LandingColors.background,
      child: Column(
        children: [
          const PhoneStatusBar(color: LandingColors.teal),
          Container(
            height: 98,
            color: LandingColors.teal,
            padding: const EdgeInsets.fromLTRB(13, 4, 13, 12),
            child: Column(
              children: [
                Row(
                  children: [
                    const CircleAvatar(
                      radius: 13,
                      backgroundColor: Color(0x40FFFFFF),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            LocaleKeys.landingPhoneWelcome,
                            style: const TextStyle(
                              color: Color(0xBFFFFFFF),
                              fontSize: 8,
                            ),
                          ),
                          Text(
                            LocaleKeys.landingPhoneTenantName,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      width: 25,
                      height: 25,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.notifications_none_rounded,
                        size: 13,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
                const Spacer(),
                Container(
                  height: 30,
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(9),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.search_rounded,
                        size: 13,
                        color: LandingColors.subtext,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          LocaleKeys.landingPhoneSearchHint,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 8.5,
                            color: LandingColors.subtext,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(11, 12, 11, 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    LocaleKeys.landingPhoneNearbyProperties,
                    style: const TextStyle(
                      color: LandingColors.navy,
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  PhonePropertyCard(
                    title: LocaleKeys.landingPhonePropertyOneTitle,
                    area: LocaleKeys.landingPhonePropertyOneArea,
                    rooms: '3',
                    price: '3,500',
                    color: const Color(0xFFCBD5E1),
                  ),
                  const SizedBox(height: 8),
                  PhonePropertyCard(
                    title: LocaleKeys.landingPhonePropertyTwoTitle,
                    area: LocaleKeys.landingPhonePropertyTwoArea,
                    rooms: '1',
                    price: '2,200',
                    color: const Color(0xFFBFDBFE),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
