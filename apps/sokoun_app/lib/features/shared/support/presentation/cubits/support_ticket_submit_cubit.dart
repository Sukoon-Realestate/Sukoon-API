part of '../../imports.dart';

class SupportTicketSubmitCubit extends AsyncCubit<SupportTicketContent> {
  SupportTicketSubmitCubit() : super(const SupportTicketContent.initial());
  Future<SupportTicketContent?> submit(SupportTicketBody body) async {
    if (isClosed || isLoading) return null;
    SupportTicketContent? created;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<SupportTicketContent>(
          api: ApiConstants.supportTickets,
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
          isFromData: body.attachments.isNotEmpty,
          mapper: (json) => SupportTicketContent.fromJson(supportMap(json)),
        ),
      ),
      onSuccess: (response) {
        ObjectBoxCacheService.remove(
          SupportTicketsData.cacheKey(body.workspace),
        );
        if (response.data.id.isNotEmpty) created = response.data;
      },
    );
    return isClosed ? null : created;
  }
}
