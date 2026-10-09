import 'dart:async';
import 'package:dropinity/custom_drop_down/dropinity.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';
import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import '../extensions/padding_extension.dart';
import '../local_db/objectbox_cache_service.dart';
import '../local_db/read_cache_policy.dart';
import '../network/account_session.dart';
import 'app_text.dart';
import 'custom_loading.dart';

typedef AppDropinityLocal<Model> = AppDropinity<void, Model>;

enum DropinityType { local, api }

class AppDropinity<FullResponse, Model> extends StatefulWidget {
  final DropinityController? controller;
  final String? Function(Model?)? validator;
  final double? listHeight;
  final DropinityType type;
  final String hint;
  final String title;
  final Model? initialValue;
  final List<Model>? values;
  final FutureOr<void> Function(Model value) onChanged;
  final Future<FullResponse> Function(BuildContext context, int page)?
  asyncCall;
  final Future<FullResponse> Function(
    BuildContext context,
    int page,
    String search,
  )?
  asyncSearchCall;
  final String Function(Model element) getLabel;

  const AppDropinity({
    super.key,
    this.listHeight,
    this.controller,
    this.validator,
    this.initialValue,
    required this.hint,
    required this.title,
    required this.values,
    required this.getLabel,
    required this.onChanged,
  }) : asyncCall = null,
       asyncSearchCall = null,
       type = DropinityType.local,
       cacheKey = null,
       cachePolicy = null,
       cacheToJson = null,
       cacheFromJson = null;

  final String? cacheKey;
  final ReadCachePolicy? cachePolicy;
  final Map<String, dynamic> Function(Model item)? cacheToJson;
  final Model Function(Map<String, dynamic> json)? cacheFromJson;

  const AppDropinity.withApiRequest({
    super.key,
    this.listHeight,
    this.controller,
    this.validator,
    this.initialValue,
    required this.hint,
    required this.title,
    required this.asyncCall,
    required this.getLabel,
    required this.onChanged,
    this.cacheKey,
    this.cachePolicy,
    this.cacheToJson,
    this.cacheFromJson,
  }) : values = null,
       asyncSearchCall = null,
       type = DropinityType.api;

  const AppDropinity.withApiSearchRequest({
    super.key,
    this.listHeight,
    this.controller,
    this.validator,
    this.initialValue,
    required this.hint,
    required this.title,
    required this.asyncSearchCall,
    required this.getLabel,
    required this.onChanged,
  }) : values = null,
       asyncCall = null,
       type = DropinityType.api,
       cacheKey = null,
       cachePolicy = null,
       cacheToJson = null,
       cacheFromJson = null;

  @override
  State<AppDropinity<FullResponse, Model>> createState() =>
      _AppDropinityState<FullResponse, Model>();
}

class _AppDropinityState<FullResponse, Model>
    extends State<AppDropinity<FullResponse, Model>> {
  late final DropinityController dropinityController;
  PagifyController<Model>? _pagifyController;
  TextEditingController? _searchController;
  Timer? _searchDebounce;

  @override
  void initState() {
    dropinityController = widget.controller ?? DropinityController();
    if (widget.type == DropinityType.api) {
      _pagifyController = PagifyController<Model>();
    }
    if (widget.asyncSearchCall != null) {
      _searchController = TextEditingController()
        ..addListener(_onSearchChanged);
    }
    super.initState();
  }

  void _onSearchChanged() {
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 400), () {
      if (!mounted) {
        return;
      }
      unawaited(_pagifyController!.refresh());
    });
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _searchController?.dispose();
    _pagifyController?.dispose();
    dropinityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    switch (widget.type) {
      case DropinityType.local:
        return Dropinity<void, Model>(
          controller: dropinityController,
          showNoDataAlert: false,
          autoValidateMode: AutovalidateMode.always,
          listHeight: widget.listHeight,
          dropdownTitle: AppText(
            widget.title,
            fontWeight: FontWeight.bold,
            fontSize: 11.sp,
          ),
          buttonData: ButtonData(
            hint: AppText(
              widget.hint,
              color: Theme.of(context).extension<AppColorTheme>() == null
                  ? Colors.grey
                  : context.appColor(AppColors.sokoonMuted),
              fontSize: 12.sp,
            ),
            initialValue: widget.initialValue,
            color: Theme.of(context).extension<AppColorTheme>() == null
                ? Colors.grey[50]
                : context.appColor(AppColors.white, surface: true),
            buttonBorderRadius: ConstantManager.buttonBorderRadius,
            selectedItemWidget: (e) =>
                AppText(widget.getLabel.call(e as Model)),
            // collapsedListIcon: const SvgPic(assetName: Assets.svgArrowDown)
          ),
          textFieldData: TextFieldData(
            controller: _searchController,
            onSearch: widget.asyncSearchCall != null
                ? (pattern, element) => true
                : (pattern, element) => widget.getLabel
                      .call(element as Model)
                      .toLowerCase()
                      .contains((pattern ?? '').toLowerCase()),
            suffixIcon: const Icon(Icons.search),
            title: LocaleKeys.search,
          ),
          onChanged: widget.onChanged,
          values: widget.values,
          valuesData: ValuesData(
            itemBuilder: (context, i, e) => AppText(
              widget.getLabel.call(e),
              textAlign: TextAlign.start,
            ).paddingBottom(5.h),
          ),
        );

      default:
        final hasCacheConfig =
            widget.cachePolicy?.persist != false &&
            widget.cacheKey != null &&
            widget.cacheToJson != null &&
            widget.cacheFromJson != null;

        final int generation = AccountSession.generation;
        final String cacheScope = ReadCacheContext.scope;
        void onSaveCache(String key, List<Map<String, dynamic>> items) {
          if (mounted &&
              generation == AccountSession.generation &&
              cacheScope == ReadCacheContext.scope) {
            ObjectBoxCacheService.save(key, {
              'items': items,
            }, policy: widget.cachePolicy);
          }
        }

        List<Map<String, dynamic>>? onReadCache(String key) {
          if (!mounted ||
              generation != AccountSession.generation ||
              cacheScope != ReadCacheContext.scope) {
            return null;
          }
          final cached = ObjectBoxCacheService.read(
            key,
            policy: widget.cachePolicy,
          );
          if (cached == null) return null;
          return (cached['items'] as List?)?.cast<Map<String, dynamic>>();
        }

        return Dropinity<FullResponse, Model>.withApiRequest(
          showNoDataAlert: false,
          validator: widget.validator,
          controller: dropinityController,
          listHeight: widget.listHeight,
          maintainState: false,
          dropdownTitle: AppText(
            widget.title,
            fontWeight: FontWeight.bold,
            fontSize: 11.sp,
          ),
          buttonData: ButtonData(
            hint: AppText(
              widget.hint,
              color: Theme.of(context).extension<AppColorTheme>() == null
                  ? Colors.grey
                  : context.appColor(AppColors.sokoonMuted),
              fontSize: 12.sp,
            ),
            initialValue: widget.initialValue,
            color: Theme.of(context).extension<AppColorTheme>() == null
                ? Colors.grey[50]
                : context.appColor(AppColors.white, surface: true),
            buttonBorderRadius: ConstantManager.buttonBorderRadius,
            selectedItemWidget: (e) =>
                AppText(widget.getLabel.call(e as Model)),
            // collapsedListIcon: const SvgPic(assetName: Assets.svgArrowDown)
          ),
          textFieldData: TextFieldData(
            controller: _searchController,
            onSearch: widget.asyncSearchCall != null
                ? (pattern, element) => true
                : (pattern, element) => widget.getLabel
                      .call(element as Model)
                      .toLowerCase()
                      .contains((pattern ?? '').toLowerCase()),
            suffixIcon: const Icon(Icons.search),
            title: LocaleKeys.search,
          ),
          onChanged: (val) {
            widget.onChanged.call(val);
          },
          onCollapse: () => _searchDebounce?.cancel(),
          pagifyData: DropinityPagifyData(
            controller: _pagifyController,
            cacheKey: hasCacheConfig ? widget.cacheKey : null,
            cacheToJson: hasCacheConfig ? widget.cacheToJson : null,
            cacheFromJson: hasCacheConfig ? widget.cacheFromJson : null,
            onSaveCache: hasCacheConfig ? onSaveCache : null,
            onReadCache: hasCacheConfig ? onReadCache : null,
            loadingBuilder: CustomLoading.showLoadingView(),
            asyncCall: widget.asyncSearchCall == null
                ? widget.asyncCall!
                : (context, page) => widget.asyncSearchCall!(
                    context,
                    page,
                    _searchController!.text.trim(),
                  ),
            mapper: (response) => PagifyData(
              data: response as List<Model>,
              paginationData: PaginationData(totalPages: 1, perPage: 10),
            ),
            errorMapper: PagifyErrorMapper(
              errorWhenDio: (e) {
                final String? msg = e.response?.data['msg'];
                return PagifyApiRequestException(
                  msg ?? 'network error occur',
                  pagifyFailure: RequestFailureData(
                    statusCode: e.response?.statusCode,
                    statusMsg: e.response?.statusMessage,
                  ),
                );
              },
            ),
            itemBuilder: (context, data, index, element) => AppText(
              widget.getLabel.call(element),
              textAlign: TextAlign.start,
            ).paddingBottom(5.h),
          ),
        );
    }
  }
}
