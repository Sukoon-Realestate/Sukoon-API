import 'package:flutter/material.dart';
import 'package:pinch_zoom/pinch_zoom.dart';

import '../scaffolds/app_scaffold.dart';
import 'cached_image.dart';

class ImageView extends StatelessWidget {
  const ImageView({
    super.key,
    required this.url,
    this.minScale = 0.0,
    this.maxScale = 1.0,
  });

  final String url;
  final double minScale;
  final double maxScale;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      body: SafeArea(
        child: Container(
          constraints: BoxConstraints.expand(
            height: MediaQuery.of(context).size.height / 2,
          ),
          child: PinchZoom(
            maxScale: 2.5,
            child: CachedImage(
              url: url,
              fit: BoxFit.fill,
            ),
            // onZoomStart: (){print('Start zooming');},
            // onZoomEnd: (){print('Stop zooming');},
          ),
        ),
      ), appBarTitle: '',
    );
  }
}
