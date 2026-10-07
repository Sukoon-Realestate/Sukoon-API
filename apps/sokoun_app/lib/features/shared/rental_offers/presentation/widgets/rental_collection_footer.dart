import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';

/// Paging remains owned by AppPagify, even when a loaded page has no matches.
class RentalCollectionFooter extends StatelessWidget {
  const RentalCollectionFooter({
    super.key,
    required this.hasMorePages,
    required this.isLoading,
    required this.onLoadMore,
    this.errorMessage,
  });

  final bool hasMorePages;
  final bool isLoading;
  final VoidCallback onLoadMore;
  final String? errorMessage;

  @override
  Widget build(BuildContext context) => hasMorePages
      ? Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (errorMessage?.isNotEmpty == true) AppText(errorMessage!),
            OutlinedButton.icon(
              onPressed: isLoading ? null : onLoadMore,
              icon: const Icon(Icons.expand_more_rounded),
              label: AppText(
                errorMessage == null
                    ? LocaleKeys.rentalCategoryLoadMore
                    : LocaleKeys.rentalCategoryRetryPage,
              ),
            ),
          ],
        )
      : const SizedBox.shrink();
}
