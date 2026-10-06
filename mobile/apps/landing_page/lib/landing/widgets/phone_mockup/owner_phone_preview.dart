import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';
import 'owner_request_row.dart';
import 'phone_status_bar.dart';

class OwnerPhonePreview extends StatelessWidget {
  const OwnerPhonePreview({super.key});

  static List<(String, String, IconData)> get _metrics => [
    ('1,234', LocaleKeys.landingPhoneViews, Icons.visibility_outlined),
    ('8', LocaleKeys.landingPhoneVisitRequests, Icons.calendar_today_outlined),
    ('12', LocaleKeys.landingPhoneMessages, Icons.chat_bubble_outline_rounded),
    ('3', LocaleKeys.landingPhoneActiveProperties, Icons.home_outlined),
  ];

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: LandingColors.background,
      child: Column(
        children: [
          const PhoneStatusBar(color: LandingColors.gold),
          Container(
            height: 73,
            color: LandingColors.gold,
            padding: const EdgeInsets.symmetric(horizontal: 13),
            child: Row(
              children: [
                const CircleAvatar(
                  radius: 13,
                  backgroundColor: Color(0x40FFFFFF),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        LocaleKeys.landingPhoneOwnerDashboard,
                        style: const TextStyle(
                          color: Color(0xBFFFFFFF),
                          fontSize: 8,
                        ),
                      ),
                      Text(
                        LocaleKeys.landingPhoneOwnerName,
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
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.notifications_none_rounded,
                    size: 13,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(11),
              child: Column(
                children: [
                  GridView.count(
                    physics: const NeverScrollableScrollPhysics(),
                    shrinkWrap: true,
                    crossAxisCount: 2,
                    mainAxisSpacing: 8,
                    crossAxisSpacing: 8,
                    childAspectRatio: 1.38,
                    children: _metrics
                        .map(
                          (metric) => Container(
                            padding: const EdgeInsets.all(9),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(9),
                              border: Border.all(color: LandingColors.border),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Icon(
                                  metric.$3,
                                  color: LandingColors.gold,
                                  size: 15,
                                ),
                                Text(
                                  metric.$1,
                                  style: const TextStyle(
                                    color: LandingColors.navy,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                                Text(
                                  metric.$2,
                                  style: const TextStyle(
                                    color: LandingColors.subtext,
                                    fontSize: 7,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                        .toList(),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: LandingColors.border),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          LocaleKeys.landingPhoneRecentRequests,
                          style: const TextStyle(
                            color: LandingColors.navy,
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 6),
                        OwnerRequestRow(
                          name: LocaleKeys.landingPhoneRequestOne,
                        ),
                        const Divider(height: 8, color: LandingColors.border),
                        OwnerRequestRow(
                          name: LocaleKeys.landingPhoneRequestTwo,
                        ),
                      ],
                    ),
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
