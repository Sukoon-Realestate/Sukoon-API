import 'dart:async';
import 'package:dropinity/custom_drop_down/dropinity.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import '../../../generated/assets.dart';
import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import '../extensions/padding_extension.dart';
import '../local_db/objectbox_cache_service.dart';
import 'app_text.dart';
import 'custom_loading.dart';
import 'svg_pic.dart';

typedef AppDropinityLocal<Model> = AppDropinity<void, Model>;
enum DropinityType{local, api}
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
  final Future<FullResponse> Function(BuildContext context, int page)? asyncCall;
  final String Function(Model element) getLabel;

  const AppDropinity({super.key,
    this.listHeight,
    this.controller,
    this.validator,
    this.initialValue,
    required this.hint,
    required this.title,
    required this.values,
    required this.getLabel,
    required this.onChanged,
  }) : asyncCall = null, type = DropinityType.local,
       cacheKey = null, cacheToJson = null, cacheFromJson = null;

  final String? cacheKey;
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
    this.cacheToJson,
    this.cacheFromJson,
}) : values = null, type = DropinityType.api;

  @override
  State<AppDropinity<FullResponse, Model>> createState() => _AppDropinityState<FullResponse, Model>();
}

class _AppDropinityState<FullResponse, Model> extends State<AppDropinity<FullResponse,Model>> {

  late final DropinityController dropinityController;

  @override
  void initState() {
    dropinityController = widget.controller ?? DropinityController();
    super.initState();
  }

  @override
  void dispose() {
    dropinityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    switch(widget.type){
      case DropinityType.local:
        return Dropinity<void, Model>(
          controller: dropinityController,
          showNoDataAlert: false,
          autoValidateMode: AutovalidateMode.always,
          listHeight: widget.listHeight,
          dropdownTitle: AppText(widget.title, fontWeight: FontWeight.bold, fontSize: 11.sp),
          buttonData: ButtonData(
              hint: AppText(widget.hint, color: Colors.grey, fontSize: 12.sp,),
              initialValue: widget.initialValue,
              color: Colors.grey[50],
              buttonBorderRadius: ConstantManager.buttonBorderRadius,
              selectedItemWidget: (e) => AppText(widget.getLabel.call(e!)),
              collapsedListIcon: const SvgPic(assetName: Assets.svgArrowDown)
          ),
          textFieldData: TextFieldData(
            onSearch: (pattern, e) => widget.getLabel.call(e!).contains(pattern??''),
            suffixIcon: const Icon(Icons.search),
            title: LocaleKeys.search,
          ),
          onChanged: widget.onChanged,
          values: widget.values,
          valuesData: ValuesData(itemBuilder: (context, i, e) => AppText(
              widget.getLabel.call(e),
              textAlign: TextAlign.start
          ).paddingBottom(5.h)),
        );

      default:
        final hasCacheConfig = widget.cacheKey != null &&
            widget.cacheToJson != null &&
            widget.cacheFromJson != null;

        void onSaveCache(String key, List<Map<String, dynamic>> items) =>
            ObjectBoxCacheService.save(key, {'items': items});

        List<Map<String, dynamic>>? onReadCache(String key) {
          final cached = ObjectBoxCacheService.read(key);
          if (cached == null) return null;
          return (cached['items'] as List?)?.cast<Map<String, dynamic>>();
        }

        return Dropinity<FullResponse, Model>.withApiRequest(
          showNoDataAlert: false,
          validator: widget.validator,
          controller: dropinityController,
          listHeight: widget.listHeight,
          maintainState: false,
          dropdownTitle: AppText(widget.title, fontWeight: FontWeight.bold, fontSize: 11.sp),
          buttonData: ButtonData(
              hint: AppText(widget.hint, color: Colors.grey, fontSize: 12.sp,),
              initialValue: widget.initialValue,
              color: Colors.grey[50],
              buttonBorderRadius: ConstantManager.buttonBorderRadius,
              selectedItemWidget: (e) => AppText(widget.getLabel.call(e!)),
              collapsedListIcon: const SvgPic(assetName: Assets.svgArrowDown)
          ),
          textFieldData: TextFieldData(
            onSearch: (pattern, e) => widget.getLabel.call(e!).contains(pattern??''),
            suffixIcon: const Icon(Icons.search),
            title: LocaleKeys.search,
          ),
          onChanged: (val) {
            widget.onChanged.call(val);
          },
          pagifyData: DropinityPagifyData(
            cacheKey: hasCacheConfig ? widget.cacheKey : null,
            cacheToJson: hasCacheConfig ? widget.cacheToJson : null,
            cacheFromJson: hasCacheConfig ? widget.cacheFromJson : null,
            onSaveCache: hasCacheConfig ? onSaveCache : null,
            onReadCache: hasCacheConfig ? onReadCache : null,
            loadingBuilder: CustomLoading.showLoadingView(),
            asyncCall: widget.asyncCall!,
            mapper: (response) => PagifyData(
                data: response as List<Model>,
                paginationData: PaginationData(
                  totalPages: 1,
                  perPage: 10,
                )
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
                }
            ),
            itemBuilder: (context, data, index, element) => AppText(
                widget.getLabel.call(element),
                textAlign: TextAlign.start
            ).paddingBottom(5.h),
          ),
        );
    }
  }
}
