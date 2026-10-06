import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../../data/enums/public_page.dart';
import '../../data/models/public_page_content.dart';
import '../cubits/public_page_cubit.dart';
import '../widgets/public_page_body.dart';
import '../widgets/public_page_empty_state.dart';
import '../public_page_labels.dart';

class PublicPageScreen extends StatefulWidget {
  const PublicPageScreen({super.key, required this.page});
  final PublicPage page;
  @override
  State<PublicPageScreen> createState() => _PublicPageScreenState();
}

class _PublicPageScreenState extends State<PublicPageScreen> {
  late final PublicPageCubit _cubit;
  late final String _language;
  @override
  void initState() {
    super.initState();
    _language = Languages.currentLanguage.locale.languageCode;
    _cubit = PublicPageCubit();
    _load();
  }

  Future<void> _load() => _cubit.load(page: widget.page, language: _language);
  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _cubit,
    child: AppScaffold(
      title: publicPageTitle(widget.page),
      body: StatusBuilder<PublicPageCubit, PublicPageContent>.withShimmer(
        initialDataForShimmer: const PublicPageContent.initial(),
        onRetry: _load,
        builder: (page) => page.content.trim().isEmpty && _cubit.state.isSuccess
            ? const PublicPageEmptyState()
            : PublicPageBody(
                page: page,
                showAppIdentity: widget.page == PublicPage.aboutUs,
              ),
      ).withPullRefresher(onRefresh: _load),
    ),
  );
}
