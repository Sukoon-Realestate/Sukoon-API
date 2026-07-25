import 'package:flutter/material.dart';

import '../../models/landing_content.dart';
import '../phone_mockup/phone_mockup.dart';

class HeroPhones extends StatelessWidget {
  const HeroPhones({required this.phoneWidth, super.key});

  final double phoneWidth;

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.ltr,
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Transform.translate(
          offset: const Offset(0, 20),
          child: PhoneMockup(audience: Audience.tenant, width: phoneWidth),
        ),
        SizedBox(width: phoneWidth * 0.1),
        Transform.translate(
          offset: const Offset(0, -10),
          child: PhoneMockup(audience: Audience.owner, width: phoneWidth),
        ),
      ],
    );
  }
}
