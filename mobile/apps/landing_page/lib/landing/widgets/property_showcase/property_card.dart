import 'package:flutter/material.dart';

import '../../models/landing_content.dart';
import '../../theme/landing_theme.dart';
import 'property_card_details.dart';
import 'property_card_media.dart';

class PropertyCard extends StatefulWidget {
  const PropertyCard({
    required this.property,
    required this.onDetails,
    super.key,
  });

  final PropertyItem property;
  final VoidCallback onDetails;

  @override
  State<PropertyCard> createState() => _PropertyCardState();
}

class _PropertyCardState extends State<PropertyCard> {
  var _saved = false;
  var _hovering = false;

  @override
  Widget build(BuildContext context) {
    final property = widget.property;
    return MouseRegion(
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      child: AnimatedContainer(
        duration: Duration(
          milliseconds: MediaQuery.disableAnimationsOf(context) ? 0 : 180,
        ),
        transform: Matrix4.translationValues(0, _hovering ? -4 : 0, 0),
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: LandingColors.border),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: _hovering ? 0.09 : 0.05),
              blurRadius: _hovering ? 24 : 16,
              offset: Offset(0, _hovering ? 8 : 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PropertyCardMedia(
              property: property,
              isSaved: _saved,
              onFavoriteToggle: () => setState(() => _saved = !_saved),
            ),
            PropertyCardDetails(
              property: property,
              onDetails: widget.onDetails,
            ),
          ],
        ),
      ),
    );
  }
}
