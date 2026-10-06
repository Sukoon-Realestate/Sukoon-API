part of '../../imports.dart';

class SupportReplyCubit extends AsyncCubit<SupportTicketContent> {
  SupportReplyCubit() : super(const SupportTicketContent.initial());
  Future<SupportTicketContent?> reply({
    required String id,
    required String body,
    required AppWorkspace workspace,
  }) async {
    if (isClosed || isLoading || body.trim().isEmpty) return null;
    SupportTicketContent? updated;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<SupportTicketContent>(
          api: ApiConstants.supportTicketReplies(id),
          httpRequestType: HttpRequestType.post,
          body: {'body': body.trim()},
          mapper: (json) => SupportTicketContent.fromJson(supportMap(json)),
        ),
      ),
      onSuccess: (response) {
        if (response.data.id == id) updated = response.data;
        ObjectBoxCacheService.remove('support_ticket_${workspace.name}_$id');
        ObjectBoxCacheService.remove(SupportTicketsData.cacheKey(workspace));
      },
    );
    return isClosed ? null : updated;
  }
}
