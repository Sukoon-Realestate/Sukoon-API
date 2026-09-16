import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import '../../data/models/chat_content.dart';

class CreateConversationCubit extends AsyncCubit<ConversationContent> {
  CreateConversationCubit() : super(const ConversationContent.initial());

  Future<void> createOrGet({
    required String userId,
    required void Function(ConversationContent conversation) onSuccess,
  }) async {
    if (isLoading || userId.trim().isEmpty) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<ConversationContent>(
          api: ApiConstants.createChatConversation,
          httpRequestType: HttpRequestType.post,
          body: {'user_id': userId},
          mapper: (json) => ConversationContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
        ),
      ),
      onSuccess: (response) => onSuccess(response.data),
    );
  }
}

/// Reference-style name for the cubit that creates or resolves a chat.
class StartChatCubit extends CreateConversationCubit {}
