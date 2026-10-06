import 'package:flutter/material.dart';

import '../../config/res/config_imports.dart';

extension MarginExtension on Widget {
  Widget margin(EdgeInsetsGeometry margin) {
    return Container(
      margin: margin,
      child: this,
    );
  }

  Widget marginSymmetric({
    double? horizontal,
    double? vertical,
  }) {
    return Container(
      margin: EdgeInsets.symmetric(
        horizontal: horizontal ?? ConstantManager.zeroAsDouble,
        vertical: vertical ?? ConstantManager.zeroAsDouble,
      ),
      child: this,
    );
  }

  Widget marginAll(double margin) {
    return Container(
      margin: EdgeInsets.all(margin),
      child: this,
    );
  }

  Widget marginLeft(double margin) {
    return Container(
      margin: EdgeInsets.only(left: margin),
      child: this,
    );
  }

  Widget marginRight(double margin) {
    return Container(
      margin: EdgeInsets.only(right: margin),
      child: this,
    );
  }

  Widget marginTop(double margin) {
    return Container(
      margin: EdgeInsets.only(top: margin),
      child: this,
    );
  }

  Widget marginBottom(double margin) {
    return Container(
      margin: EdgeInsets.only(bottom: margin),
      child: this,
    );
  }

  Widget marginStart(double margin) {
    return Container(
      margin: EdgeInsetsDirectional.only(start: margin),
      child: this,
    );
  }

  Widget marginEnd(double margin) {
    return Container(
      margin: EdgeInsetsDirectional.only(end: margin),
      child: this,
    );
  }

  Widget marginOnly({
    double? left,
    double? right,
    double? top,
    double? bottom,
  }) {
    return Container(
      margin: EdgeInsets.only(
        left: left ?? 0.0,
        right: right ?? 0.0,
        top: top ?? 0.0,
        bottom: bottom ?? 0.0,
      ),
      child: this,
    );
  }

  Widget marginOnlyDirectional({
    double? start,
    double? end,
    double? top,
    double? bottom,
  }) {
    return Container(
      margin: EdgeInsetsDirectional.only(
        start: start ?? 0.0,
        end: end ?? 0.0,
        top: top ?? 0.0,
        bottom: bottom ?? 0.0,
      ),
      child: this,
    );
  }
}
