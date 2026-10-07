import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import '../../data/models/listing_ai_facts.dart';
import '../../data/models/listing_suggestion.dart';
import '../screens/listing_ai_screen.dart';

class ListingAiEntry extends StatelessWidget {
  const ListingAiEntry({
    super.key,
    required this.form,
    required this.onApplied,
    this.propertyId = '',
  });
  final OwnerAddPropertyFormState form;
  final String propertyId;
  final ValueChanged<ListingSuggestion> onApplied;
  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    onPressed: () async {
      final result = await Go.to<ListingSuggestion>(
        ListingAiScreen(
          propertyId: propertyId,
          facts: ListingAiFacts.fromForm(form),
          canApply: true,
        ),
      );
      if (result != null && context.mounted) onApplied(result);
    },
    icon: const Icon(Icons.auto_awesome_outlined),
    label: AppText(LocaleKeys.paidAiAssistant),
  );
}
