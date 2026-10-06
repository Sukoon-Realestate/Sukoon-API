import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import 'property_photo_tile.dart';

typedef _DepartingPhoto = ({OwnerPropertyPhotoDraft photo, int index});

/// Keeps each photo's identity while its position changes and its removal fades.
class AnimatedPropertyPhotoGrid extends StatefulWidget {
  const AnimatedPropertyPhotoGrid({
    super.key,
    required this.photos,
    required this.onAddPhotos,
    required this.onRemovePhoto,
    required this.onReplacePhoto,
    required this.onMainPhotoSelected,
    this.onPhotoMoved,
  });

  final List<OwnerPropertyPhotoDraft> photos;
  final VoidCallback onAddPhotos;
  final ValueChanged<int> onRemovePhoto;
  final ValueChanged<int> onReplacePhoto;
  final ValueChanged<int> onMainPhotoSelected;
  final ValueChanged<({int from, int to})>? onPhotoMoved;

  @override
  State<AnimatedPropertyPhotoGrid> createState() =>
      _AnimatedPropertyPhotoGridState();
}

class _AnimatedPropertyPhotoGridState extends State<AnimatedPropertyPhotoGrid> {
  // The add control also retains its identity when photos move around it.
  static const _addTileId = 'property-add-photo';
  final ValueNotifier<Map<String, _DepartingPhoto>> _departingPhotos =
      ValueNotifier({});
  final Map<String, Timer> _removalTimers = {};

  @override
  void didUpdateWidget(covariant AnimatedPropertyPhotoGrid oldWidget) {
    super.didUpdateWidget(oldWidget);
    final incomingIds = widget.photos.map((photo) => photo.id).toSet();
    final departures = Map.of(_departingPhotos.value);
    for (final id in incomingIds) {
      departures.remove(id);
      _removalTimers.remove(id)?.cancel();
    }
    final duration = SokounMotion.duration(context, milliseconds: 220);
    if (duration != Duration.zero) {
      for (final (index, photo) in oldWidget.photos.indexed) {
        if (incomingIds.contains(photo.id)) continue;
        departures[photo.id] = (photo: photo, index: index);
        _removalTimers.remove(photo.id)?.cancel();
        _removalTimers[photo.id] = Timer(duration, () {
          _removalTimers.remove(photo.id);
          if (!mounted) return;
          _departingPhotos.value = Map.of(_departingPhotos.value)
            ..remove(photo.id);
        });
      }
    }
    _departingPhotos.value = departures;
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (SokounMotion.duration(context) != Duration.zero) return;
    for (final timer in _removalTimers.values) {
      timer.cancel();
    }
    _removalTimers.clear();
    _departingPhotos.value = {};
  }

  @override
  void dispose() {
    for (final timer in _removalTimers.values) {
      timer.cancel();
    }
    _departingPhotos.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final horizontalGap = 10.w;
      final verticalGap = 10.h;
      final columns = math.max(
        1,
        (constraints.maxWidth / (180 + horizontalGap)).ceil(),
      );
      final extent =
          (constraints.maxWidth - horizontalGap * (columns - 1)) / columns;
      final moveDuration = SokounMotion.duration(context, milliseconds: 360);
      final removeDuration = SokounMotion.duration(context, milliseconds: 220);
      final canAdd = Validators.canAddPropertyPhoto(widget.photos.length);

      Widget position({
        required String photoId,
        required int index,
        required Widget child,
      }) => AnimatedPositionedDirectional(
        key: ValueKey(photoId),
        duration: moveDuration,
        curve: SokounMotion.curve,
        start: (index % columns) * (extent + horizontalGap),
        top: (index ~/ columns) * (extent + verticalGap),
        width: extent,
        height: extent,
        child: child,
      );

      Widget tile(
        OwnerPropertyPhotoDraft photo,
        int index, {
        bool leaving = false,
      }) => position(
        photoId: photo.id,
        index: index,
        child: AbsorbPointer(
          absorbing: leaving,
          child: ExcludeSemantics(
            excluding: leaving,
            child: AnimatedOpacity(
              opacity: leaving ? 0 : 1,
              duration: removeDuration,
              curve: SokounMotion.curve,
              child: AnimatedScale(
                scale: leaving ? .86 : 1,
                duration: removeDuration,
                curve: SokounMotion.curve,
                child: PhotoTile(
                  photo: photo,
                  onMoveEarlier: widget.onPhotoMoved == null || index == 0
                      ? null
                      : () =>
                            widget.onPhotoMoved!((from: index, to: index - 1)),
                  onMoveLater:
                      widget.onPhotoMoved == null ||
                          index == widget.photos.length - 1
                      ? null
                      : () =>
                            widget.onPhotoMoved!((from: index, to: index + 1)),
                  isMainPhoto: index == 0,
                  onReplacePhoto: () => widget.onReplacePhoto(index),
                  onRemovePhoto: photo.canRemove
                      ? () => widget.onRemovePhoto(index)
                      : null,
                  onMainPhotoSelected: index == 0
                      ? null
                      : () => widget.onMainPhotoSelected(index),
                ),
              ),
            ),
          ),
        ),
      );

      return ValueListenableBuilder<Map<String, _DepartingPhoto>>(
        valueListenable: _departingPhotos,
        builder: (context, departures, _) {
          var lastIndex = widget.photos.length - (canAdd ? 0 : 1);
          for (final departure in departures.values) {
            lastIndex = math.max(lastIndex, departure.index);
          }
          final rows = (lastIndex + 1 + columns - 1) ~/ columns;
          final height = rows * extent + math.max(0, rows - 1) * verticalGap;
          final grid = SizedBox(
            height: height,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                for (final (index, photo) in widget.photos.indexed)
                  if (index != 0) tile(photo, index),
                if (canAdd)
                  position(
                    photoId: _addTileId,
                    index: widget.photos.length,
                    child: PhotoTile(onAddPhotos: widget.onAddPhotos),
                  ),
                // The cover travels above its neighbors instead of behind them.
                if (widget.photos.isNotEmpty) tile(widget.photos.first, 0),
                for (final departure in departures.values)
                  tile(departure.photo, departure.index, leaving: true),
              ],
            ),
          );
          if (moveDuration == Duration.zero) return grid;
          return AnimatedSize(
            duration: moveDuration,
            curve: SokounMotion.curve,
            alignment: Alignment.topCenter,
            clipBehavior: Clip.none,
            child: grid,
          );
        },
      );
    },
  );
}
