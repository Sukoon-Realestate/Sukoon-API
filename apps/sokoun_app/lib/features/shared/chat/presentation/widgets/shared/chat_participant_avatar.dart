import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class ChatParticipantAvatar extends StatelessWidget {
  const ChatParticipantAvatar({
    super.key,
    required this.name,
    required this.avatarUrl,
    required this.size,
    this.backgroundColor = AppColors.mintLight,
    this.iconColor = AppColors.sokoonTeal,
  });

  final String name;
  final String avatarUrl;
  final double size;
  final Color backgroundColor;
  final Color iconColor;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      image: true,
      label: name,
      child: SizedBox.square(
        dimension: size,
        child: ClipOval(
          child: avatarUrl.isEmpty
              ? _AvatarFallback(
                  backgroundColor: backgroundColor,
                  iconColor: iconColor,
                  iconSize: size * .48,
                )
              : Image.network(
                  avatarUrl,
                  fit: BoxFit.cover,
                  excludeFromSemantics: true,
                  errorBuilder: (context, error, stackTrace) => _AvatarFallback(
                    backgroundColor: backgroundColor,
                    iconColor: iconColor,
                    iconSize: size * .48,
                  ),
                ),
        ),
      ),
    );
  }
}

class _AvatarFallback extends StatelessWidget {
  const _AvatarFallback({
    required this.backgroundColor,
    required this.iconColor,
    required this.iconSize,
  });

  final Color backgroundColor;
  final Color iconColor;
  final double iconSize;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: backgroundColor,
      child: Center(
        child: Icon(
          Icons.person_outline_rounded,
          color: iconColor,
          size: iconSize,
        ),
      ),
    );
  }
}
