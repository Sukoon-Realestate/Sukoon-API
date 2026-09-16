import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';

import '../../data/chats_data.dart';
import '../../data/models/chat_content.dart';

/// Loads the conversation summaries used by the normal chat list.
class GetChatsCubit extends AsyncCubit<List<ConversationContent>> {
  GetChatsCubit({ChatDataSource? dataSource})
    : _dataSource = dataSource ?? ChatData.source,
      super(const <ConversationContent>[]);

  final ChatDataSource _dataSource;

  Future<void> getChat() => getChats();

  Future<void> getChats() async {
    if (isLoading) return;
    setLoading();
    try {
      final (List<ConversationContent> firstPage, pagination) =
          await _dataSource.getConversationsPage(page: 1);
      final List<ConversationContent> conversations = <ConversationContent>[
        ...firstPage,
      ];
      for (int page = 2; page <= pagination.totalPages; page++) {
        final (List<ConversationContent> nextPage, _) = await _dataSource
            .getConversationsPage(page: page);
        conversations.addAll(nextPage);
      }
      setSuccess(
        BaseModel<List<ConversationContent>>(
          key: '',
          msg: '',
          data: conversations,
        ),
      );
    } catch (error) {
      setError(errorMessage: error.toString());
    }
  }

  void resetUnreadMessagesCount(int index) {
    if (index < 0 || index >= state.data.length) return;
    final List<ConversationContent> conversations = List.of(state.data);
    conversations[index] = conversations[index].copyWith(unreadCount: 0);
    setSuccess(
      BaseModel<List<ConversationContent>>(
        key: '',
        msg: '',
        data: conversations,
      ),
    );
  }
}
