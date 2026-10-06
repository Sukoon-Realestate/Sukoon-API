import 'package:flutter/material.dart';

class FooterColumn extends StatelessWidget {
  const FooterColumn({
    required this.title,
    required this.links,
    required this.onNavigate,
    super.key,
  });

  final String title;
  final List<(String, String)> links;
  final ValueChanged<String> onNavigate;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 12),
        ...links.map(
          (link) => TextButton(
            onPressed: () => onNavigate(link.$2),
            style: TextButton.styleFrom(
              foregroundColor: Colors.white.withValues(alpha: 0.55),
              padding: const EdgeInsets.symmetric(vertical: 5),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: Text(link.$1, style: const TextStyle(fontSize: 14)),
          ),
        ),
      ],
    );
  }
}
