part of '../../imports.dart';

class SupportHelpCubit extends AsyncCubit<SupportHelpContent> {
  SupportHelpCubit() : super(const SupportHelpContent.initial());
  Future<void> load({
    required AppWorkspace workspace,
    required String language,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<SupportHelpContent>(
          api: ApiConstants.supportHelpCenter,
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          queryParameters: {'workspace': workspace.name, 'lang': language},
          cacheKey: 'support_help_${workspace.name}_$language',
          mapper: (json) => SupportHelpContent.fromJson(supportMap(json)),
          fromCacheJson: SupportHelpContent.fromJson,
          toJson: (data) => data.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
