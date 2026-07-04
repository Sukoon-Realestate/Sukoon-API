import 'dart:async';
import 'package:flutter/material.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/pagify.dart';
import 'chat_message.dart';
import 'message_widget.dart';

class ChatBody<Response> extends StatelessWidget {
  final MainAxisAlignment Function(bool isFromMe) messageAlignment;
  final PagifyController<ChatMessages> controller;
  final Future<Response> Function(BuildContext context, int currentPage) asyncCall;
  final PagifyData<ChatMessages> Function(Response response) mapper;
  final PagifyErrorMapper errorMapper;
  final Widget? loadingBuilder;
  final Widget Function(PagifyException e)? errorBuilder;
  final Widget Function(ChatMessages message) rightMessageBuilder;
  final Widget Function(ChatMessages message) leftMessageBuilder;
  final double? cacheExtent;
  final double? itemExtent;
  final String? noConnectionText;
  final Widget? emptyView;
  final FutureOr<void> Function()? onLoading;
  final FutureOr<void> Function(BuildContext, int, PagifyException)? onError;
  final FutureOr<void> Function(BuildContext, List<ChatMessages>)? onSuccess;
  final FutureOr<void> Function(bool isConnect)? onConnectivityChanged;

  const ChatBody({super.key,
    required this.controller,
    required this.asyncCall,
    required this.mapper,
    required this.errorMapper,
    required this.rightMessageBuilder,
    required this.leftMessageBuilder,
    required this.messageAlignment,
    this.onLoading,
    this.onError,
    this.onSuccess,
    this.onConnectivityChanged,
    this.errorBuilder,
    this.loadingBuilder,
    this.cacheExtent,
    this.itemExtent,
    this.noConnectionText,
    this.emptyView,
  });

  @override
  Widget build(BuildContext context) {
    return Pagify<Response, ChatMessages>.listView(
      isReverse: true,
      shrinkWrap: true,
      onLoading: onLoading,
      onError: onError,
      onSuccess: onSuccess,
      onConnectivityChanged: onConnectivityChanged,
      noConnectionText: noConnectionText,
      emptyListView: emptyView,
      cacheExtent: cacheExtent,
      itemExtent: itemExtent,
      loadingBuilder: loadingBuilder,
      controller: controller,
      asyncCall: asyncCall,
      mapper: mapper,
      ignoreErrorBuilderWhenErrorOccursAndListIsNotEmpty: true,
      errorMapper: errorMapper,
      errorBuilder: errorBuilder,
      itemBuilder: (context, data, index, element) => Row(
        mainAxisAlignment: messageAlignment(element.sender.isFromMe),
        children: [
          MessageWidget(
            message: element,
            leftMessageBuilder: leftMessageBuilder,
            rightMessageBuilder: rightMessageBuilder,
          ),
        ],
      ),
    );
  }
}