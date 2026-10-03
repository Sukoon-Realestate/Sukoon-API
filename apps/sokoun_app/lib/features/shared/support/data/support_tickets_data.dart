import 'dart:math' as math;
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import '../../../main_view/data/enums/app_workspace.dart';
import 'models/support_ticket_content.dart';
import 'support_json.dart';

abstract final class SupportTicketsData {
  static String cacheKey(AppWorkspace workspace) =>
      'support_tickets_${workspace.name}_v1';
  static Future<(List<SupportTicketContent>, PaginationData)> getPage({
    required int page,
    required AppWorkspace workspace,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        path: ApiConstants.supportTickets,
        method: RequestMethod.get,
        queryParameters: {
          'workspace': workspace.name,
          'page': page,
          'page_size': 20,
        },
      ),
      mapper: (json) => parsePage(supportMap(json), page: page),
    );
    return response.data;
  }

  static (List<SupportTicketContent>, PaginationData) parsePage(
    Map<String, dynamic> json, {
    required int page,
  }) {
    final int perPage = math.max(1, supportInt(json['per_page'], fallback: 20));
    final int totalPages = json.containsKey('total_pages')
        ? supportInt(json['total_pages'], fallback: 1)
        : json.containsKey('count')
        ? (supportInt(json['count']) / perPage).ceil()
        : json['next'] == null
        ? page
        : page + 1;
    return (
      supportList(json['results'], SupportTicketContent.fromJson),
      PaginationData(perPage: perPage, totalPages: math.max(1, totalPages)),
    );
  }
}
