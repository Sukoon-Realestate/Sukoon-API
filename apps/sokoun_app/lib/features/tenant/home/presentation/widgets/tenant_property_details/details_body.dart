import 'package:flutter/material.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';

import 'bottom_actions.dart';
import 'details_content.dart';
import 'hero_gallery.dart';

class TenantPropertyDetailsBody extends StatelessWidget {
  const TenantPropertyDetailsBody({
    super.key,
    required this.property,
    required this.isSaved,
    required this.onSavedPressed,
    this.onChatPressed,
    this.isOpeningChat = false,
  });

  final TenantPropertyDetailsContent property;
  final bool isSaved;
  final VoidCallback onSavedPressed;
  final VoidCallback? onChatPressed;
  final bool isOpeningChat;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            child: LayoutBuilder(
              builder: (context, constraints) {
                final bool wide =
                    constraints.maxWidth >= SokounLayout.detailBreakpoint &&
                    MediaQuery.textScalerOf(context).scale(14) <= 21;
                final Widget gallery = TenantPropertyHeroGallery(
                  property: property,
                );
                final Widget details = TenantPropertyDetailsContentView(
                  property: property,
                );
                return wide
                    ? Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.all(20),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(20),
                                child: gallery,
                              ),
                            ),
                          ),
                          Expanded(child: details),
                        ],
                      )
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [gallery, details],
                      );
              },
            ),
          ),
        ),
        TenantPropertyBottomActions(
          property: property,
          isSaved: isSaved,
          onSavedPressed: onSavedPressed,
          onChatPressed: onChatPressed,
          isOpeningChat: isOpeningChat,
        ),
      ],
    );
  }
}
