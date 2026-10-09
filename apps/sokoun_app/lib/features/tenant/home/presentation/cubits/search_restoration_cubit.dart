import 'package:melos_core/config/language/languages.dart';
import 'package:sokoun_app/features/shared/recovery/data/private_recovery_data.dart';
import 'package:sokoun_app/features/shared/recovery/data/recovery_scope.dart';
import 'package:sokoun_app/features/shared/recovery/presentation/cubits/draft_cubit.dart';
import '../../data/models/search_restoration_snapshot.dart';

class SearchRestorationCubit extends DraftCubit<SearchRestorationSnapshot> {
  SearchRestorationCubit()
    : super(
        PrivateDraftStore(
          scope: () => RecoveryScope.current(
            flow: 'search_restoration',
            entityId: Languages.currentLanguage.languageCode,
            workspace: 'tenant',
          ),
          encode: (value) => value.toJson(),
          decode: SearchRestorationSnapshot.fromJson,
        ),
      );
}
