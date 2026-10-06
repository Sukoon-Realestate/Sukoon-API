import 'dart:async';
import 'package:flutter/material.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';

import 'chat_message.dart';
import 'message_widget.dart';

class EasyChat<Response> extends StatelessWidget {
  final PagifyController<ChatMessages> controller;
  final MainAxisAlignment Function(bool isFromMe) messageAlignment;
  final Future<Response> Function(BuildContext context, int currentPage)
  asyncCall;
  final PagifyData<ChatMessages> Function(Response response) mapper;
  final PagifyErrorMapper errorMapper;
  final Widget? loadingBuilder;
  final Widget Function(PagifyException e)? errorBuilder;
  final Widget Function(ChatMessages message) rightMessageBuilder;
  final Widget Function(ChatMessages message) leftMessageBuilder;

  /// A header for a chronological boundary (for example a new message day).
  final Widget? Function(List<ChatMessages> messages, int index)?
  itemHeaderBuilder;
  final double? cacheExtent;
  final double? itemExtent;
  final String? noConnectionText;
  final Widget? emptyView;
  final FutureOr<void> Function()? onLoading;
  final FutureOr<void> Function(BuildContext, int, PagifyException)? onError;
  final FutureOr<void> Function(BuildContext, List<ChatMessages>)? onSuccess;
  final FutureOr<void> Function(bool isConnect)? onConnectivityChanged;
  final String? cacheKey;
  final Map<String, dynamic> Function(ChatMessages item)? cacheToJson;
  final ChatMessages Function(Map<String, dynamic> json)? cacheFromJson;

  const EasyChat({
    super.key,
    required this.controller,
    required this.asyncCall,
    required this.mapper,
    required this.errorMapper,
    required this.rightMessageBuilder,
    required this.leftMessageBuilder,
    required this.messageAlignment,
    this.errorBuilder,
    this.itemHeaderBuilder,
    this.loadingBuilder,
    this.cacheExtent,
    this.itemExtent,
    this.onLoading,
    this.onError,
    this.onSuccess,
    this.onConnectivityChanged,
    this.noConnectionText,
    this.emptyView,
    this.cacheKey,
    this.cacheToJson,
    this.cacheFromJson,
  });

  @override
  Widget build(BuildContext context) {
    return AppPagify<ChatMessages>(
      noConnectionText: noConnectionText,
      isReverse: true,
      emptyListView: emptyView,
      onLoading: onLoading,
      onError: onError,
      onSuccess: onSuccess,
      onConnectivityChanged: onConnectivityChanged,
      cacheExtent: cacheExtent,
      itemExtent: itemExtent,
      errorMapper: errorMapper,
      asyncCall: (context, page) async {
        final PagifyData<ChatMessages> mapped = mapper(
          await asyncCall(context, page),
        );
        return (mapped.data, mapped.paginationData);
      },
      pagifyController: controller,
      errorBuilder: errorBuilder,
      loadingBuilder: loadingBuilder,
      cacheKey: cacheKey,
      cacheToJson: cacheToJson,
      cacheFromJson: cacheFromJson,
      itemBuilder: (context, data, index, message) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (itemHeaderBuilder?.call(data, index) case final Widget header)
            header,
          Row(
            mainAxisAlignment: messageAlignment(message.sender.isFromMe),
            children: [
              MessageWidget(
                message: message,
                leftMessageBuilder: leftMessageBuilder,
                rightMessageBuilder: rightMessageBuilder,
              ),
            ],
          ),
        ],
      ),
    );
  }
}
