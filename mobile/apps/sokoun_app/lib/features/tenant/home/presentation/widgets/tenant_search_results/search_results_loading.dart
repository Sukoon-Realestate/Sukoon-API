import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

/// A passive skeleton: mounting it must never start the paginated request.
class SearchResultsLoading extends StatelessWidget {
  const SearchResultsLoading({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        Container(
          height: 48,
          color: context.appColor(AppColors.white, surface: true),
        ),
        const SizedBox(height: 20),
        for (int index = 0; index < 3; index++)
          Container(
            height: 200,
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: context.appColor(AppColors.white, surface: true),
              borderRadius: BorderRadius.circular(16),
            ),
          ),
      ],
    );
  }
}
