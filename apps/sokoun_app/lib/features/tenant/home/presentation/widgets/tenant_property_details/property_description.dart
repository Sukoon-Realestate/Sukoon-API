import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

class PropertyDescription extends StatefulWidget {
  const PropertyDescription({super.key, required this.description});

  final String description;

  @override
  State<PropertyDescription> createState() => _PropertyDescriptionState();
}

class _PropertyDescriptionState extends State<PropertyDescription> {
  final ValueNotifier<bool> _expanded = ValueNotifier(false);

  @override
  void didUpdateWidget(covariant PropertyDescription oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.description != widget.description) _expanded.value = false;
  }

  @override
  void dispose() {
    _expanded.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final style = AppTextStyles.regular14.copyWith(
        fontSize: 14,
        height: 1.5,
        color: AppColors.sokoonGray,
      );
      final painter = TextPainter(
        text: TextSpan(text: widget.description, style: style),
        textDirection: Directionality.of(context),
        textScaler: MediaQuery.textScalerOf(context),
        maxLines: 4,
      )..layout(maxWidth: constraints.maxWidth);
      final bool canExpand = painter.didExceedMaxLines;
      painter.dispose();
      return ValueListenableBuilder<bool>(
        valueListenable: _expanded,
        builder: (context, expanded, _) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AnimatedSize(
              duration: SokounMotion.duration(context, milliseconds: 260),
              curve: SokounMotion.curve,
              alignment: AlignmentDirectional.topStart,
              child: Text(
                widget.description,
                style: style,
                maxLines: expanded ? null : 4,
                overflow: expanded
                    ? TextOverflow.visible
                    : TextOverflow.ellipsis,
              ),
            ),
            if (canExpand)
              Semantics(
                expanded: expanded,
                child: TextButton.icon(
                  onPressed: () => _expanded.value = !expanded,
                  icon: AnimatedRotation(
                    turns: expanded ? .5 : 0,
                    duration: SokounMotion.duration(context),
                    child: const Icon(Icons.expand_more_rounded, size: 20),
                  ),
                  label: Text(
                    expanded ? LocaleKeys.showLess : LocaleKeys.showMore,
                    style: AppTextStyles.base,
                  ),
                ),
              ),
          ],
        ),
      );
    },
  );
}
