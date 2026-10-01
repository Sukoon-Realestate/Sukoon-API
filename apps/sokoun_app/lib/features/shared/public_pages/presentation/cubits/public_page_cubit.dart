import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import '../../data/enums/public_page.dart';
import '../../data/models/public_page_content.dart';

class PublicPageCubit extends AsyncCubit<PublicPageContent> {
  PublicPageCubit() : super(const PublicPageContent.initial());

  Future<void> load({
    required PublicPage page,
    required String language,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PublicPageContent>(
          api: page.endpoint,
          httpRequestType: HttpRequestType.get,
          queryParameters: {'lang': language},
          cacheKey: 'public_page_${page.name}_$language',
          mapper: (json) => PublicPageContent.fromJson(
            Map<String, dynamic>.from(json as Map),
          ),
          fromCacheJson: PublicPageContent.fromJson,
          toJson: (content) => content.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
