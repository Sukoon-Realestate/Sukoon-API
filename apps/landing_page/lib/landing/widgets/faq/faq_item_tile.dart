import 'package:flutter/material.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';

class FaqItemTile extends StatelessWidget {
  const FaqItemTile({
    required this.item,
    required this.isOpen,
    required this.onTap,
    super.key,
  });

  final FaqItem item;
  final bool isOpen;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: LandingColors.border)),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: onTap,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 18),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      item.question,
                      style: const TextStyle(
                        color: LandingColors.navy,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  AnimatedContainer(
                    duration: Duration(
                      milliseconds: MediaQuery.disableAnimationsOf(context)
                          ? 0
                          : 180,
                    ),
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: isOpen
                          ? LandingColors.teal
                          : LandingColors.softSurface,
                      shape: BoxShape.circle,
                    ),
                    child: AnimatedRotation(
                      duration: Duration(
                        milliseconds: MediaQuery.disableAnimationsOf(context)
                            ? 0
                            : 180,
                      ),
                      turns: isOpen ? 0.5 : 0,
                      child: Icon(
                        Icons.keyboard_arrow_down_rounded,
                        size: 18,
                        color: isOpen ? Colors.white : LandingColors.subtext,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          AnimatedCrossFade(
            firstChild: Padding(
              padding: const EdgeInsets.only(bottom: 18),
              child: Align(
                alignment: AlignmentDirectional.centerStart,
                child: Text(
                  item.answer,
                  style: const TextStyle(
                    color: LandingColors.subtext,
                    fontSize: 15,
                    height: 1.8,
                  ),
                ),
              ),
            ),
            secondChild: const SizedBox(width: double.infinity),
            crossFadeState: isOpen
                ? CrossFadeState.showFirst
                : CrossFadeState.showSecond,
            duration: Duration(
              milliseconds: MediaQuery.disableAnimationsOf(context) ? 0 : 180,
            ),
          ),
        ],
      ),
    );
  }
}
