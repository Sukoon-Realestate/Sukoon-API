import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/enums/app_workspace.dart';
import '../../data/workspace_preferences.dart';

class WorkspaceCubit extends Cubit<AppWorkspace> {
  WorkspaceCubit() : super(AppWorkspace.tenant);

  static WorkspaceCubit get instance => injector<WorkspaceCubit>();

  String? _userId;
  String? get userId => _userId;

  void initialize(String? userId) {
    if (_userId == userId) return;
    _userId = userId;
    emit(
      userId == null ? AppWorkspace.tenant : WorkspacePreferences.read(userId),
    );
  }

  Future<void> switchTo(AppWorkspace workspace) async {
    final String? id = _userId;
    if (id == null || workspace == state) return;
    emit(workspace);
    await WorkspacePreferences.write(id, workspace);
  }

  void reset() {
    _userId = null;
  }
}
