import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../../data/models/decision_notebook.dart';
import '../cubits/decision_tools_cubit.dart';
import '../widgets/decision_notebook_view.dart';

class DecisionToolsScreen extends StatefulWidget {
  const DecisionToolsScreen({super.key});
  @override
  State<DecisionToolsScreen> createState() => _DecisionToolsScreenState();
}

class _DecisionToolsScreenState extends State<DecisionToolsScreen> {
  late final DecisionToolsCubit _cubit;
  late final ValueNotifier<Future<void>> _request;
  @override
  void initState() {
    super.initState();
    _cubit = DecisionToolsCubit(accountId: UserModel.currentUser?.id ?? '');
    _request = ValueNotifier(_cubit.load());
  }

  @override
  void dispose() {
    _request.dispose();
    _cubit.close();
    super.dispose();
  }

  Future<void> _reload() async {
    _request.value = _cubit.load();
    await _request.value;
  }

  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.freeDecisionTools,
    showBackButton: true,
    body: ValueListenableBuilder<Future<void>>(
      valueListenable: _request,
      builder: (context, request, _) => FutureBuilder<void>(
        future: request,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return ExceptionView(
              msg: LocaleKeys.freeLocalSaveFailed,
              onRetry: _reload,
            );
          }
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          return BlocBuilder<DecisionToolsCubit, DecisionNotebook>(
            bloc: _cubit,
            builder: (context, notebook) => SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: DecisionNotebookView(
                notebook: notebook,
                cubit: _cubit,
                onReturned: _reload,
              ),
            ),
          );
        },
      ),
    ),
  );
}
