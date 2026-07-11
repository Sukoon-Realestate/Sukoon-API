import 'dart:convert';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'network_request.dart';

class FireStoreService{
  final String _collectionName = 'requests';
  final String _requestCollection = 'request';
  final String _responseCollection = 'response';
  final String _errorsCollection = 'errors';
  late final _fireStoreMainCollection = FirebaseFirestore.instance.collection(_collectionName);

  FireStoreService._internal();
  static FireStoreService? _instance;
  static FireStoreService get instance => _instance ??= FireStoreService._internal();

  static bool get isInitialized => _instance != null;

  String _docId(String path) => path.replaceAll("/", "-");
  Future<void> storeRequest(NetworkRequest request)async{
    _fireStoreMainCollection
        .doc(_docId(request.path))
        .collection(_requestCollection)
        .add(request.toJson());
  }

  Future<void> storeError(String error)async{
    await FirebaseFirestore.instance
        .collection(_errorsCollection)
        .add({'error' : error});
  }

  Future<void> storeResponse({
    required String path,
    required Map<String, dynamic> response,
  })async{
    _fireStoreMainCollection
        .doc(_docId(path))
        .collection(_responseCollection)
        .add(jsonDecode(jsonEncode(response).replaceAll("/", "-")));
  }

  Future<List<NetworkRequest>?> getRequestData<T>(String path)async{
    final requests = await _fireStoreMainCollection
        .doc(_docId(path))
        .collection(_requestCollection)
        .get();

    if(requests.docs.isEmpty) return null;
    final List<NetworkRequest> data = [];
    for(QueryDocumentSnapshot<Map<String, dynamic>> doc in requests.docs){
      data.add(NetworkRequest.fromJson(doc.data()));
    }

    return data;
  }

  Future<List<T>?> getRequestResponseData<T>({
    required String path,
    required T Function(Map<String, dynamic> data) mapper
  })async{
    final responses = await _fireStoreMainCollection
        .doc(_docId(path))
        .collection(_responseCollection)
        .get();

    if(responses.docs.isEmpty) return null;
    final List<T> data = [];
    for(QueryDocumentSnapshot<Map<String, dynamic>> doc in responses.docs){
      data.add(mapper(doc.data()));
    }

    return data;
  }

  Future<void> clear(String path)async =>
      await _fireStoreMainCollection.doc(_docId(path)).delete();

  bool isServiceEnabled = true;

  void enableService() {
    FireStoreService.instance;
  }

  void disableService() {
    _instance = null;
  }
}