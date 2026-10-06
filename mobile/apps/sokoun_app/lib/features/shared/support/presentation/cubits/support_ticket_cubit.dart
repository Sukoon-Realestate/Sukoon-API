part of '../../imports.dart';

class SupportTicketCubit extends AsyncCubit<SupportTicketContent> {
  SupportTicketCubit() : super(const SupportTicketContent.initial());
  String? _cacheKey;
  Future<void> load({
    required String id,
    required AppWorkspace workspace,
  }) async {
    if (isClosed || isLoading) return;
    final cacheKey = 'support_ticket_${workspace.name}_$id';
    _cacheKey = cacheKey;
    SupportTicketContent mapTicket(Map<String, dynamic> json) {
      final ticket = SupportTicketContent.fromJson(json);
      if (ticket.id != id) {
        throw const FormatException('Invalid support ticket ID');
      }
      return ticket;
    }

    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<SupportTicketContent>(
          api: ApiConstants.supportTicket(id),
          httpRequestType: HttpRequestType.get,
          queryParameters: {'workspace': workspace.name},
          cacheKey: cacheKey,
          mapper: (json) => mapTicket(supportMap(json)),
          fromCacheJson: mapTicket,
          toJson: (ticket) => ticket.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  void apply(SupportTicketContent ticket) {
    if (isClosed || ticket.id != data.id) return;
    updateData(ticket);
    final cacheKey = _cacheKey;
    if (cacheKey != null) ObjectBoxCacheService.save(cacheKey, ticket.toJson());
  }
}
