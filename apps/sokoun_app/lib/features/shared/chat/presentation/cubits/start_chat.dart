import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../data/models/chat_content.dart';

class CreateConversationCubit extends AsyncCubit<ConversationContent> {
  CreateConversationCubit() : super(const ConversationContent.initial());

  Future<void> createOrGet({
    required String userId,
    required void Function(ConversationContent conversation) onSuccess,
  }) async {
    if (isClosed || isLoading || userId.trim().isEmpty) return;
    if (userId == UserModel.currentUser?.id) {
      setError(errorMessage: LocaleKeys.workspaceSelfActionBlocked);
      return;
    }
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

class ChatCubit extends StartChatCubit {}
