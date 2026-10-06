import 'package:flutter/material.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';

class JourneyStepCard extends StatelessWidget {
  const JourneyStepCard({required this.step, required this.color, super.key});

  final JourneyStep step;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 230),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: LandingColors.border),
      ),
      child: Stack(
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                step.number,
                style: TextStyle(
                  color: color.withValues(alpha: 0.15),
                  fontSize: 36,
                  fontWeight: FontWeight.w900,
                  height: 1,
                ),
              ),
              const SizedBox(height: 14),
              Text(
                step.title,
                style: const TextStyle(
                  color: LandingColors.navy,
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                step.body,
                style: const TextStyle(
                  color: LandingColors.subtext,
                  fontSize: 14,
                  height: 1.7,
                ),
              ),
            ],
          ),
          Positioned(
            top: 0,
            left: 0,
            child: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(Icons.check_rounded, color: color, size: 17),
            ),
          ),
        ],
      ),
    );
  }
}
