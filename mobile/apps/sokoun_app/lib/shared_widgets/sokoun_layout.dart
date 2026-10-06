import 'package:flutter/material.dart';

/// Widths are logical layout constraints, never scaled design coordinates.
enum SokounContentWidth {
  form(520),
  readable(720),
  wide(1200),
  full(double.infinity);

  const SokounContentWidth(this.maxWidth);
  final double maxWidth;
}

class SokounContent extends StatelessWidget {
  const SokounContent({
    super.key,
    required this.child,
    this.width = SokounContentWidth.readable,
  });

  final Widget child;
  final SokounContentWidth width;

  @override
  Widget build(BuildContext context) => Align(
    alignment: Alignment.topCenter,
    heightFactor: 1,
    child: ConstrainedBox(
      constraints: BoxConstraints(maxWidth: width.maxWidth),
      child: SizedBox(width: double.infinity, child: child),
    ),
  );
}

abstract final class SokounLayout {
  static const double navigationBreakpoint = 600;
  static const double detailBreakpoint = 960;

  static int columns(
    BuildContext context,
    double width, {
    double minimumWidth = 320,
    int maximum = 3,
    double gap = 16,
  }) {
    final double textScale = MediaQuery.textScalerOf(context).scale(14) / 14;
    return ((width + gap) / (minimumWidth * textScale.clamp(1, 2) + gap))
        .floor()
        .clamp(1, maximum);
  }
}

/// For bounded sections; paginated collections continue to use AppPagify.
class SokounAdaptiveGrid extends StatelessWidget {
  const SokounAdaptiveGrid({
    super.key,
    required this.children,
    this.minimumWidth = 320,
    this.maximumColumns = 3,
    this.gap = 16,
  });

  final List<Widget> children;
  final double minimumWidth;
  final int maximumColumns;
  final double gap;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final int columns = SokounLayout.columns(
        context,
        constraints.maxWidth,
        minimumWidth: minimumWidth,
        maximum: maximumColumns,
        gap: gap,
      );
      final double width =
          (constraints.maxWidth - gap * (columns - 1)) / columns;
      return Wrap(
        spacing: gap,
        runSpacing: gap,
        children: [
          for (final Widget child in children)
            SizedBox(width: width, child: child),
        ],
      );
    },
  );
}
