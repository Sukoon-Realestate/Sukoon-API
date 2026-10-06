import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../data/models/property_location.dart';
import '../../data/models/property_location_state.dart';
import '../cubits/property_location_cubit.dart';
import '../widgets/property_location/property_location_map.dart';
import '../widgets/property_location/property_location_search.dart';
import '../widgets/property_location/property_location_controls.dart';
import '../widgets/property_location/property_location_confirmation.dart';

class PropertyLocationPickerScreen extends StatefulWidget {
  const PropertyLocationPickerScreen({
    super.key,
    this.initialLocation,
    this.initialQuery = '',
  });
  final PropertyLocation? initialLocation;
  final String initialQuery;

  @override
  State<PropertyLocationPickerScreen> createState() =>
      _PropertyLocationPickerScreenState();
}

class _PropertyLocationPickerScreenState
    extends State<PropertyLocationPickerScreen> {
  late final PropertyLocationCubit _cubit;
  final ValueNotifier<bool> _satellite = ValueNotifier(false);

  @override
  void initState() {
    super.initState();
    _cubit = PropertyLocationCubit();
    _cubit.initialize(widget.initialLocation);
    if (widget.initialLocation == null &&
        widget.initialQuery.trim().isNotEmpty) {
      _cubit.search(widget.initialQuery);
    }
  }

  @override
  void dispose() {
    _cubit.close();
    _satellite.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _cubit,
    child: AppScaffold(
      title: LocaleKeys.ownerAddPropertyMapTitle,
      contentWidth: SokounContentWidth.wide,
      body: SafeArea(
        child:
            BlocBuilder<
              PropertyLocationCubit,
              AsyncState<PropertyLocationState>
            >(
              builder: (context, state) => LayoutBuilder(
                builder: (context, constraints) {
                  final search = PropertyLocationSearch(
                    initialQuery: widget.initialQuery,
                    state: state.data,
                    busy: state.isLoading,
                  );
                  final map = ValueListenableBuilder<bool>(
                    valueListenable: _satellite,
                    builder: (context, satellite, _) => PropertyLocationMap(
                      selected: state.data.selected,
                      satellite: satellite,
                      onSelected: _cubit.select,
                    ),
                  );
                  final controls = ValueListenableBuilder<bool>(
                    valueListenable: _satellite,
                    builder: (context, satellite, _) =>
                        PropertyLocationControls(
                          satellite: satellite,
                          busy: state.isLoading,
                          onLocate: _cubit.locate,
                          onToggleSatellite: () =>
                              _satellite.value = !satellite,
                        ),
                  );
                  final confirmation = PropertyLocationConfirmation(
                    selected: state.data.selected,
                    busy: state.isLoading,
                  );
                  if (constraints.maxWidth >= 760) {
                    return Row(
                      children: [
                        Expanded(child: map),
                        SizedBox(
                          width: 340,
                          child: ListView(
                            children: [search, controls, confirmation],
                          ),
                        ),
                      ],
                    );
                  }
                  return Column(
                    children: [
                      ConstrainedBox(
                        constraints: BoxConstraints(
                          maxHeight: constraints.maxHeight * .32,
                        ),
                        child: SingleChildScrollView(child: search),
                      ),
                      Expanded(child: map),
                      ConstrainedBox(
                        constraints: BoxConstraints(
                          maxHeight: constraints.maxHeight * .42,
                        ),
                        child: SingleChildScrollView(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [controls, confirmation],
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
      ),
    ),
  );
}
