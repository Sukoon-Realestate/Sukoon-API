import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../theme/landing_theme.dart';

class ResponsiveGrid extends StatelessWidget {
  const ResponsiveGrid({
    required this.children,
    super.key,
    this.desktopColumns = 4,
    this.tabletColumns = 2,
    this.spacing = 20,
    this.runSpacing = 20,
    this.minItemWidth = 240,
  });

  final List<Widget> children;
  final int desktopColumns;
  final int tabletColumns;
  final double spacing;
  final double runSpacing;
  final double minItemWidth;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final preferredColumns = switch (width) {
          < LandingBreakpoints.mobile => 1,
          < LandingBreakpoints.tablet => tabletColumns,
          _ => desktopColumns,
        };
        final widthBasedColumns = math.max(
          1,
          ((width + spacing) / (minItemWidth + spacing)).floor(),
        );
        final columns = math.min(preferredColumns, widthBasedColumns);
        final itemWidth = (width - spacing * (columns - 1)) / columns;

        return Wrap(
          spacing: spacing,
          runSpacing: runSpacing,
          children: children
              .map((child) => SizedBox(width: itemWidth, child: child))
              .toList(),
        );
      },
    );
  }
}
