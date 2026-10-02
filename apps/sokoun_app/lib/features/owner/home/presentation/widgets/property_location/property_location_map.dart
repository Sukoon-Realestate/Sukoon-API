import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_map_style.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import '../../../data/models/property_location.dart';

class PropertyLocationMap extends StatefulWidget {
  const PropertyLocationMap({
    super.key,
    required this.selected,
    required this.satellite,
    required this.onSelected,
  });
  final PropertyLocation? selected;
  final bool satellite;
  final ValueChanged<PropertyLocation> onSelected;

  @override
  State<PropertyLocationMap> createState() => _PropertyLocationMapState();
}

class _PropertyLocationMapState extends State<PropertyLocationMap> {
  GoogleMapController? _controller;
  static LatLng _point(PropertyLocation location) =>
      LatLng(location.latitude, location.longitude);

  @override
  void didUpdateWidget(covariant PropertyLocationMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    final location = widget.selected;
    if (location != null &&
        (location.latitude != oldWidget.selected?.latitude ||
            location.longitude != oldWidget.selected?.longitude)) {
      _moveTo(location);
    }
  }

  Future<void> _moveTo(PropertyLocation location) async {
    final controller = _controller;
    if (controller == null) return;
    final update = CameraUpdate.newLatLngZoom(_point(location), 17);
    try {
      if (SokounMotion.duration(context) == Duration.zero) {
        await controller.moveCamera(update);
      } else {
        await controller.animateCamera(update);
      }
    } catch (_) {
      // Route disposal can race a native camera animation.
    }
  }

  void _select(LatLng point) => widget.onSelected(
    PropertyLocation(latitude: point.latitude, longitude: point.longitude),
  );

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => GoogleMap(
    initialCameraPosition: CameraPosition(
      target: _point(widget.selected ?? const PropertyLocation.initial()),
      zoom: widget.selected == null ? 11 : 17,
    ),
    style: widget.satellite ? null : SokounMapStyle.light,
    mapType: widget.satellite ? MapType.hybrid : MapType.normal,
    onMapCreated: (controller) {
      _controller = controller;
      final selected = widget.selected;
      if (selected != null) _moveTo(selected);
    },
    onTap: _select,
    onLongPress: _select,
    markers: {
      if (widget.selected case final location?)
        Marker(
          markerId: const MarkerId('property-location'),
          position: _point(location),
          draggable: true,
          onDragEnd: _select,
          icon: BitmapDescriptor.defaultMarkerWithHue(
            HSVColor.fromColor(AppColors.sokoonGold).hue,
          ),
          infoWindow: InfoWindow(
            title: LocaleKeys.ownerAddPropertySelectedLocation,
          ),
        ),
    },
    mapToolbarEnabled: false,
    zoomControlsEnabled: true,
    compassEnabled: true,
    tiltGesturesEnabled: false,
    myLocationButtonEnabled: false,
  );
}
