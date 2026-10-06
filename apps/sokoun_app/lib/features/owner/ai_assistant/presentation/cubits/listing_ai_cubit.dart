import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import '../../data/models/listing_suggestion.dart';
import '../../data/models/listing_ai_body.dart';

class ListingAiCubit extends PremiumMutationCubit<ListingSuggestion> {
  ListingAiCubit() : super(const ListingSuggestion.initial());
  Future<ListingSuggestion?> generate(ListingAiBody body) =>
      !const ['ar', 'en'].contains(body.language) || body.requestKey.isEmpty
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.aiSuggestions,
            body: body.toJson(),
            fromJson: ListingSuggestion.fromJson,
            valid: (suggestion) =>
                suggestion.id.isNotEmpty &&
                (body.propertyId.isEmpty ||
                    suggestion.propertyId == body.propertyId) &&
                suggestion.suggestedTitle.trim().isNotEmpty &&
                suggestion.suggestedDescription.trim().isNotEmpty &&
                suggestion.suggestedTitle.length <= 150 &&
                suggestion.suggestedDescription.length <= 5000,
          ),
        );
}
