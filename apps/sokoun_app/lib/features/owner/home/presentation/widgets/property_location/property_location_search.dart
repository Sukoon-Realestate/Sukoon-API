import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/models/property_location_state.dart';
import '../../../data/property_location_data.dart';
import '../../cubits/property_location_cubit.dart';

class PropertyLocationSearch extends StatefulWidget {
  const PropertyLocationSearch({
    super.key,
    required this.initialQuery,
    required this.state,
    required this.busy,
  });
  final String initialQuery;
  final PropertyLocationState state;
  final bool busy;

  @override
  State<PropertyLocationSearch> createState() => _PropertyLocationSearchState();
}

class _PropertyLocationSearchState extends State<PropertyLocationSearch> {
  late final TextEditingController _controller;
  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialQuery);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _search() {
    // The search icon is inside the field, so outside-tap dismissal won't run.
    FocusManager.instance.primaryFocus?.unfocus();
    context.read<PropertyLocationCubit>().search(_controller.text);
  }

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<PropertyLocationCubit>();
    final failure = widget.state.failure;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        DefaultTextField(
          controller: _controller,
          action: TextInputAction.search,
          onSubmitted: (_) => _search(),
          onChanged: (_) => cubit.clearSearch(),
          decoration: InputDecoration(
            labelText: LocaleKeys.ownerAddPropertyMapSearch,
            prefixIcon: const Icon(Icons.search_rounded),
            suffixIcon: IconButton(
              tooltip: LocaleKeys.search,
              onPressed: _search,
              icon: const Icon(Icons.arrow_forward_rounded),
            ),
          ),
        ),
        if (widget.busy) const LinearProgressIndicator(),
        if (failure != null)
          Row(
            children: [
              Expanded(
                child: AppText(switch (failure) {
                  PropertyLocationFailure.serviceDisabled =>
                    LocaleKeys.locationServicesDisabled,
                  PropertyLocationFailure.permissionDenied =>
                    LocaleKeys.propertyMapPermissionDenied,
                  PropertyLocationFailure.permissionDeniedForever =>
                    LocaleKeys.propertyMapPermissionSettings,
                  PropertyLocationFailure.noResults =>
                    LocaleKeys.propertyMapNoResults,
                  PropertyLocationFailure.unavailable =>
                    LocaleKeys.propertyMapUnavailable,
                }),
              ),
              if (failure == PropertyLocationFailure.serviceDisabled ||
                  failure == PropertyLocationFailure.permissionDeniedForever)
                TextButton(
                  onPressed: cubit.openSettings,
                  child: AppText(LocaleKeys.permissionOpenSettings),
                ),
            ],
          ),
        for (final result in widget.state.results)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(
              Icons.location_on_outlined,
              color: context.appColor(AppColors.sokoonTeal),
            ),
            title: AppText(
              result.address.isEmpty ? _controller.text.trim() : result.address,
            ),
            subtitle: Text(
              result.coordinates,
              textDirection: TextDirection.ltr,
            ),
            onTap: () {
              cubit.select(result);
            },
          ),
      ],
    ).paddingAll(12.w);
  }
}
