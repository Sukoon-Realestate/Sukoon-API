import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../models/landing_content.dart';
import '../shared/imports.dart';
import 'faq_item_tile.dart';

class FaqSection extends StatefulWidget {
  const FaqSection({super.key});

  @override
  State<FaqSection> createState() => _FaqSectionState();
}

class _FaqSectionState extends State<FaqSection> {
  int? _openIndex = 0;

  @override
  Widget build(BuildContext context) {
    return SectionSpacing(
      backgroundColor: Colors.white,
      child: Column(
        children: [
          SectionHeading(
            tag: LocaleKeys.landingFaqTag,
            title: LocaleKeys.landingFaqTitle,
          ),
          const SizedBox(height: 52),
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: Column(
                children: List.generate(LandingContent.faqs.length, (index) {
                  final item = LandingContent.faqs[index];
                  final open = _openIndex == index;

                  return FaqItemTile(
                    item: item,
                    isOpen: open,
                    onTap: () =>
                        setState(() => _openIndex = open ? null : index),
                  );
                }),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
