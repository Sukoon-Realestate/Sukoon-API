# Satr Project — Core Rules & Patterns

This file documents the conventions, patterns, and APIs in `lib/src/core/` so you can build features correctly without re-reading the core every time.

---

## Architecture

Clean Architecture with three layers:
- **Domain**: `UseCase` / `UseCaseWithoutParam` → returns `Result<T, Failure>`
- **Data**: Repositories call `NetworkService` / `ObjectBoxCacheService`
- **Presentation**: Cubits extending `AsyncCubit<T>` or plain `Cubit<State>`

Dependency injection via `GetIt`: `injector<Type>()`

---

## Shared Widgets

Before creating a widget from scratch, check `packages/core/lib/core/widgets` for an existing custom widget that fits the use case. Reuse or extend the shared widget when possible so UI stays consistent across apps.

When asked to create shared UI like auth fields or social sign-in buttons:
- Put each component in its own file.
- Reuse ready components from `packages/core/lib/core/widgets` instead of building controls from scratch.
- Add app-specific colors to `packages/core/lib/config/res/color_manager.dart`.
- Add plain user-facing text to `packages/core/assets/translations/lang.json`.
- Run `dart run generate/strings/main.dart` after translation changes.

---

## Navigation — `Go` class

All navigation is done through the static `Go` class (`lib/src/core/navigation/navigator.dart`).
Never use `Navigator` directly.

```dart
// Push a page
Go.to(SomePage());

// Push with transition
Go.to(SomePage(), transitionType: TransitionType.slide);

// Push and remove current page
Go.off(SomePage());

// Push and clear entire stack
Go.offAll(SomePage());

// Named route
Go.toNamed(NamedRoutes.home);
Go.offAllNamed(NamedRoutes.login);

// Push only if not already on that route
Go.toOrOff(SomePage());

// Go back
Go.back();
Go.back(result); // with result

// Go back to root
Go.backToInitial();

// Access context anywhere
Go.context

// Available transition types
TransitionType.slide
TransitionType.fade
TransitionType.scale
TransitionType.cupertino
```

Route names are in `RouterConstants`. Always use `NamedRoutes` enum, not raw strings.

---

## Network — `NetworkService` / `DioService`

All API calls go through `NetworkService` (injected as `injector<NetworkService>()`).

### Making a request directly

```dart
final result = await networkService.callApi<MyModel>(
  NetworkRequest(
    path: ApiEndpoints.someEndpoint,
    method: RequestMethod.post,
    body: {'key': 'value'},
    queryParameters: {'page': 1},
  ),
  mapper: (json) => MyModel.fromJson(json),
);
```

### Using `BaseCrudUseCase` (preferred for standard CRUD)

```dart
final result = await baseCrudUseCase(CrudBaseParmas<MyModel>(
  api: ApiEndpoints.someEndpoint,
  httpRequestType: HttpRequestType.get,
  mapper: (json) => MyModel.fromJson(json),

  // Optional: cache to ObjectBox
  cacheKey: 'some_cache_key',
  fromCacheJson: (json) => MyModel.fromJson(json),
  toJson: (model) => model.toJson(),

  // Optional: pagination
  queryParameters: {'page': 1, 'per_page': 10},

  // Optional: file upload
  isFromData: true,
  onSendProgress: (sent, total) {},
));
```

### API Endpoints

All endpoints are static constants on `ApiEndpoints` class (`lib/src/core/network/api_endpoints.dart`).

### Request methods

```dart
RequestMethod.get
RequestMethod.post
RequestMethod.put
RequestMethod.patch
RequestMethod.delete
```

### Token management

```dart
networkService.setToken(token);   // called automatically by UserCubit.setUserLoggedIn
networkService.removeToken();      // called automatically by UserCubit.logout
```

---

## State Management — `AsyncCubit<T>`

Extend `AsyncCubit<T>` for any cubit that loads remote data.

```dart
class MyDataCubit extends AsyncCubit<List<MyModel>> {
  MyDataCubit() : super(AsyncState.initial(data: []));

  Future<void> loadData() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase(CrudBaseParmas<List<MyModel>>(
        api: ApiEndpoints.something,
        httpRequestType: HttpRequestType.get,
        mapper: (json) => (json as List).map((e) => MyModel.fromJson(e)).toList(),
      )),
      onSuccess: (model) {
        // model.data is List<MyModel>
      },
      onError: (msg) {},
      withInternetInterceptor: true, // auto-retry on reconnect
    );
  }
}
```

### State shape

```dart
state.status  // BaseStatus enum
state.data    // T
state.msg     // String? (error message)

// Checks
state.status.isInitial
state.status.isLoading
state.status.isSuccess
state.status.isError
state.status.isLoadingMore
```

### Manual state transitions (when not using executeAsyncWithBaseModel)

```dart
setLoading();
setLoadingMore();
setSuccess();          // keeps current data
updateData(newData);   // sets data only
setError();
updateErrorMessage('msg');
reset();
```

---

## Local Storage

Two storage layers:

### `CacheStorage` — SharedPreferences (non-sensitive)

```dart
// Write
CacheStorage.write(key: 'my_key', value: 'string_value');
CacheStorage.write(key: 'my_key', value: 42);
CacheStorage.write(key: 'my_key', value: true);

// Read
final String? value = CacheStorage.read<String>(key: 'my_key');
final int? num     = CacheStorage.read<int>(key: 'my_key');
final bool? flag   = CacheStorage.read<bool>(key: 'my_key');

// Delete one
CacheStorage.delete(key: 'my_key');

// Clear all
CacheStorage.deleteAll();
```

### `SecureStorage` — FlutterSecureStorage (sensitive: tokens, passwords)

```dart
// Write
await SecureStorage.write(key: 'token', value: jwtToken);

// Read
final String? token = await SecureStorage.read(key: 'token');

// Delete
await SecureStorage.delete(key: 'token');

// Clear all
await SecureStorage.deleteAll();
```

### `ObjectBoxCacheService` — Structured JSON cache (API responses)

```dart
// Init once at app start
await ObjectBoxCacheService.init();

// Save
ObjectBoxCacheService.save('cache_key', jsonMap);

// Read (returns decoded Map or null)
final Map<String, dynamic>? cached = ObjectBoxCacheService.read('cache_key');

// Clear
ObjectBoxCacheService.clearAll();
```

Cache is automatically managed by `BaseCrudUseCase` when you pass `cacheKey` + `fromCacheJson` + `toJson`.

---

## User State — `UserCubit`

```dart
// Access anywhere
final userCubit = UserCubit.instance;

// Check login status
userCubit.isUserLoggedIn  // bool

// Get user model
userCubit.user  // UserModel

// Log in (sets token in Dio, saves to storage)
await userCubit.setUserLoggedIn(user: userModel, token: token);

// Update user data
await userCubit.updateUser(updatedUserModel);

// Update token only
await userCubit.updateToken(newToken);

// Logout (clears storage, removes Dio token, clears ObjectBox)
await userCubit.logout();
```

---

## Error Handling

### Result pattern

```dart
final result = await someUseCase(params);

result.when(
  success: (data) { /* data is T */ },
  error: (failure) { /* failure.message is String */ },
);

// Or in AsyncCubit via executeAsyncWithBaseModel — preferred
```

### Failure types

```dart
ServerFailure  // extends Failure
// failure.message contains the server error message
```

### Exception types (thrown inside data layer, caught by interceptors)

```
ServerException, FetchDataException, BadRequestException,
UnauthorizedException, NotFoundException, ConflictException,
InternalServerErrorException, NoInternetConnectionException,
CacheException, ForbiddenException, BlockedException
```

---

## Validation — `Validators`

All validation returns `String?` (null = valid, string = error message in locale key format).

```dart
Validators.validateEmpty(value)
Validators.validateName(value)
Validators.validateEmail(value)
Validators.validatePhone(value)          // Saudi format: starts with 5, 9 digits
Validators.validateAge(value)            // 18-150
Validators.validateOtpCode(value)        // exactly 4 digits
Validators.validateChatMessage(value)    // Arabic+English letters only
Validators.validateDowry(min, max)
Validators.validateIdentityNumber(value)
Validators.validateEmail(value)
Validators.noValidate(value)             // only checks script injection
```

---

## Extensions — Quick Reference

### Sized spacing

```dart
16.szH   // SizedBox(height: 16.h)
16.szW   // SizedBox(width: 16.w)
```

### Padding / Margin on Widget

```dart
widget.paddingAll(16)
widget.paddingSymmetric(horizontal: 16, vertical: 8)
widget.paddingOnly(top: 8, bottom: 8)
widget.paddingStart(16)    // RTL-aware
widget.paddingEnd(16)

widget.marginAll(16)
widget.marginSymmetric(horizontal: 16)
```

### Alignment

```dart
widget.centerWidget
widget.startWidget
widget.endWidget
```

### List separator

```dart
[widget1, widget2].joinWith(Divider())
// → [widget1, Divider(), widget2]
```

### List indexed map

```dart
items.indexedMap((index, item) => ItemWidget(index: index, item: item))
```

### Sliver

```dart
widget.toSliver()  // SliverToBoxAdapter
```

### Context

```dart
context.width
context.height
context.theme
context.textTheme
context.hideKeyboard()
context.isKeyboardOpen
context.isDark
```

### TextStyle

```dart
style.bold
style.semiBold
style.medium
style.s16         // font size 16
style.primaryColor
style.setFontSize(14)
style.setHeight(1.5)
```

### Bool

```dart
someCondition.toNormalLang()  // "yes" / "no" locale key
```

### Null check

```dart
someObject.isNull
someObject.isNotNull
```

### Back N times

```dart
3.pop()  // Go.back() called 3 times
```

### Form field wrapper

```dart
widget.asFormField<String>(validator: (v) => Validators.validateEmpty(v))
```

---

## Notifications

Notification handling is in `NotificationService` + `NotificationRoutes`.
Notification types are in `NotificationType` enum.

To navigate from a notification:
```dart
// In NotificationRoutes, add a new case in the switch for your NotificationType
// Use Go.toNamed() or Go.to() inside
```

To show local notification:
```dart
// Called internally by NotificationService._showNotification()
// Configure in setupNotifications()
```

---

## Socket (Chat)

```dart
final socket = ClientIOImpl(
  url: wsUrl,
  roomId: roomId,
  events: EasyChatEvents(
    messageEvents: MessageEvents(
      receiveMsgEvent: 'receive_message',
      sendMsgEvent: 'send_message',
    ),
    chatEvents: ChatEvents(
      enterChatEvent: 'enter_chat',
      exitChatEvent: 'exit_chat',
    ),
    otherEvents: ['typing', 'read'],
  ),
  jsonToChatMessage: (json) => ChatMessage.fromJson(json),
  onReceiveMessage: (msg) async { /* handle message */ },
  enableOfflineState: true,
);

await socket.initSocket();
await socket.connect();

// Send message
await socket.sendMessage({'message': text, 'room_id': roomId});

// Emit any event
await socket.emitEvent(event: 'typing', data: {'room_id': roomId});

// Check connection
socket.isConnected

// Disconnect
await socket.disconnect();
```

---

## Video Calls — `ZegoService`

```dart
final zego = ZegoService(
  appId: Constants.zegoAppId,
  appSign: Constants.zegoAppSign,
  navigatorKey: Go.navigatorKey,
);

await zego.initZego();

await zego.onUserLogin(
  currentUserId: user.id.toString(),
  currentUserName: user.name,
  onCallEnd: (event, defaultAction) { defaultAction(); },
);

// Create call button
zego.zegoButton(
  inviteeId: otherUserId,
  inviteeName: otherUserName,
  callType: ZegoCallType.videoCall,
);

// Logout on app sign-out
await zego.onUserLogout();
```

---

## Helpers

```dart
// Image picker
final File? image = await getImage();
final List<File> images = await getImages();
final File? photo = await getImageFromCameraOrDevice(context);

// Share app
shareApp();

// URL launchers
launchURL('https://...');
launchWhatsApp(phone);
callPhone(phone);
sendMail(email);
launchInstagram(handle);

// Permissions
await checkPermission(Permission.camera);

// Device type
getDeviceType()  // 'ios' | 'android'

// Status bar
changeStatusbarColor(color: Colors.white, isDark: true);

// RTL alignment
getAlignment  // Alignment.centerRight (AR) or Alignment.centerLeft (EN)

// Localization helper
showByLang(ar: 'عربي', en: 'English')
```

---

## BaseModel / PaginationResponse

API responses are always wrapped:

```dart
// Single item response
BaseModel<T>.fromJson(json, jsonToModel: (j) => T.fromJson(j))
// .key   → API key
// .msg   → success message
// .data  → T

// Paginated list response
PaginationResponse<T>.fromJson(json,
  mapper: (list) => (list as List).map((e) => T.fromJson(e)).toList(),
  dataKey: 'items',  // optional, default 'data'
)
// .data       → List<T>?
// .pagination → Pagination?
//   .currentPage, .totalPages, .totalItems, .nextPageUrl
```

---

## Use Case Pattern

```dart
// With params
class MyUseCase extends UseCase<MyModel, MyParams> {
  @override
  Future<Result<MyModel, Failure>> call(MyParams param) async {
    return repository.doSomething(param);
  }
}

// Without params
class MyUseCase extends UseCaseWithoutParam<MyModel> {
  @override
  Future<Result<MyModel, Failure>> call() async {
    return repository.doSomething();
  }
}
```

---

## App Lifecycle

```dart
AppLifecycleService.currentState   // AppLifecycleState
AppLifecycleService.isInForeground // bool
AppLifecycleService.isInBackground // bool

// Wrap widget to react to lifecycle
AppLifecycleManager(
  onResumed: () {},
  onPaused: () {},
  child: MyWidget(),
)
```

---

## Conventions

- **ScreenUtil sizing**: always use `.w`, `.h`, `.sp` — never raw pixel values
- **Locale keys**: always use `LocaleKeys.*` — never hardcode strings
- **Injection**: `injector<Type>()` from GetIt
- **Enums**: use `is*` extension checks, not equality comparisons
- **Backend type**: `BackendConfiguation.type.isPhp` / `.isAsp`
- **Colors/Text styles**: extend via TextStyle extensions, not inline styles
- **Bloc logging**: handled by `AppBlocObserver`, no need to add manual logs

---

## Clean Code — Variable & Method Initialization Rules

These rules are derived from the actual patterns used across all features in this project.

---

### Variables

#### Rule 1 — Declare type explicitly on the left side, infer on the right

```dart
// CORRECT
final String name = json['name'] ?? '';
final List<ChatModel> items = [];
final Map<String, dynamic> body = {};

// WRONG — too vague when it matters
var name = json['name'] ?? '';
```

Only use `var` or `final` without type when the type is 100% obvious from the right side:
```dart
final result = await baseCrudUseCase.call(...);  // OK — Future result
final socket = ClientIOImpl(...);                 // OK — type is clear from constructor
```

#### Rule 2 — Use `final` for everything that never changes after assignment

```dart
// CORRECT
final int id;
final String name;
final UserModel user;

// WRONG — mutable when it doesn't need to be
String name;
int id;
```

Only use non-final for variables the cubit mutates directly:
```dart
int _currentPage = 0;      // cubit increments this
bool _isFetching = false;  // cubit toggles this
int currentIndex = 0;      // cubit updates this
```

#### Rule 3 — Use `late final` for dependencies injected in the constructor body

```dart
// CORRECT
class MyCubit extends AsyncCubit<MyModel> {
  late final BaseCrudUseCase _baseCrudUseCase;

  MyCubit() : super(MyModel.initial()) {
    _baseCrudUseCase = injector();
  }
}

// WRONG — nullable when it shouldn't be
BaseCrudUseCase? _baseCrudUseCase;
```

#### Rule 4 — Prefix private variables with `_`

```dart
// CORRECT — private to the class
late final BaseCrudUseCase _baseCrudUseCase;
int _currentPage = 0;
bool _isFetching = false;
StreamSubscription? _streamSubscription;

// CORRECT — public (accessible from outside)
late final BaseCrudUseCase baseCrudUseCase;  // AsyncCubit base exposes this
int currentIndex = 0;                        // HomeCubit exposes this
```

#### Rule 5 — Use `const` on constructors and literals that never change

```dart
// CORRECT
const TitleValueShape(title: '', value: '');
const SizedBox(height: 16);
const [MainView(), NotificationsScreen()];  // screens list in HomeCubit

// CORRECT on model fields
const ConsultantModel({required this.id, ...});
```

#### Rule 6 — Initialize to a meaningful empty value, not null

```dart
// CORRECT — empty but typed
AsyncCubit<List<MyModel>>() : super([])
AsyncCubit<String>() : super('')
AsyncCubit<int>() : super(0)
AsyncCubit<MyModel>() : super(MyModel.initial())

// WRONG — lazy null that forces null checks everywhere
AsyncCubit<List<MyModel>>() : super(null)
```

If null is genuinely needed (optional data not yet loaded), use `super(null)` with a nullable generic: `AsyncCubit<MyModel?>`.

#### Rule 7 — Nullable fields in models use `?`, not default values

```dart
// CORRECT — field may or may not come from API
final String? email;
final Kinship? relation;
final File? image;

// CORRECT — field always comes from API
final int id;
final String name;
```

Use `?? ''` or `?? 0` only in `fromJson` when the API may omit the field:
```dart
name: json['name'] ?? '',
count: json['count'] ?? 0,
```

---

### Methods

#### Rule 8 — Always declare async methods as `Future<void>` (not `void`)

```dart
// CORRECT
Future<void> login(LoginBody body) async { ... }
Future<void> logout() async { ... }

// WRONG — hides the async nature
void login(LoginBody body) async { ... }
```

Exception: fire-and-forget event handlers in widgets (`onTap: () async { ... }`) stay as closures.

#### Rule 9 — Use named parameters for everything beyond one argument

```dart
// CORRECT
Future<void> completeProfile({
  required IndividualUserModel body,
  required void Function() onSuccess,
}) async { ... }

// WRONG — positional args hide intent at call site
Future<void> completeProfile(IndividualUserModel body, void Function() onSuccess) async { ... }
```

Single-argument methods may use positional:
```dart
void setSocket(SocketHelper socket) => emit(socket);
void changeIndex(int index) { ... }
```

#### Rule 10 — Callback parameters use `void Function(T)` or `FutureOr<void> Function(T)?`

```dart
// CORRECT — required callback (always called on success)
required void Function(UserModel data) onSuccess

// CORRECT — optional callback
FutureOr<void> Function()? onSuccess
FutureOr<void> Function(String msg)? onError

// WRONG — too generic
required Function onSuccess
required dynamic Function(dynamic) callback
```

Use `FutureOr` when the callback might need to `await` something:
```dart
FutureOr<void> Function()? cancelOnTap  // caller may or may not await
```

#### Rule 11 — Private helpers use `_` prefix and a descriptive verb name

```dart
// CORRECT
String _getEndPoint() { ... }
String _getChatType(ChatType type) { ... }
bool _canLoadMore() { ... }

// WRONG — no underscore, or vague name
String endpoint() { ... }
String helper() { ... }
```

#### Rule 12 — Getters replace zero-arg methods that only read state

```dart
// CORRECT — derived values from state
MatchRequest? get matchRequest => state.data.matchRequest;
Stage? get currentStage => matchRequest?.stage;
bool get canLoadMore => _currentPage < state.data.$2.totalPages;
bool get isLoading => state.isLoading;

// WRONG — method when a getter is appropriate
MatchRequest? getMatchRequest() => state.data.matchRequest;
bool getIsLoading() => state.isLoading;
```

#### Rule 13 — Single-expression methods use `=>` (fat arrow)

```dart
// CORRECT
void setSocket(SocketHelper socket) => emit(socket);
bool get isLoading => state.isLoading;
String get userName => state.data.name ?? '';

// WRONG — block body for a one-liner
void setSocket(SocketHelper socket) {
  emit(socket);
}
```

Use a block body as soon as there is more than one expression.

#### Rule 14 — Always `await` calls to `executeAsyncWithBaseModel`

```dart
// CORRECT
Future<void> loadData() async {
  await executeAsyncWithBaseModel(
    operation: () => baseCrudUseCase.call(...),
  );
}

// WRONG — unawaited, caller can't track completion
Future<void> loadData() async {
  executeAsyncWithBaseModel(...);
}
```

#### Rule 15 — `operation:` closure returns the use-case call directly (no extra wrapper when possible)

```dart
// CORRECT — direct return
operation: () => baseCrudUseCase.call(CrudBaseParmas(...))

// CORRECT — async needed only when you must await before calling
operation: () async => await baseCrudUseCase.call<UserModel>(CrudBaseParmas(...))

// WRONG — unnecessary async/await wrapping
operation: () async {
  return await baseCrudUseCase.call(CrudBaseParmas(...));
}
```

---

### Models

#### Rule 16 — Every model needs: constructor + `fromJson` + `toJson` + `copyWith` + `initial`

```dart
class MyModel extends Equatable {
  final int id;
  final String name;

  const MyModel({required this.id, required this.name});

  // Empty state — used as AsyncCubit initial data
  factory MyModel.initial() => const MyModel(id: 0, name: '');

  // Deserialize from API
  factory MyModel.fromJson(Map<String, dynamic> json) => MyModel(
    id: json['id'] ?? 0,
    name: json['name'] ?? '',
  );

  // Serialize to API / cache
  Map<String, dynamic> toJson() => {'id': id, 'name': name};

  // Immutable update
  MyModel copyWith({int? id, String? name}) => MyModel(
    id: id ?? this.id,
    name: name ?? this.name,
  );

  @override
  List<Object?> get props => [id, name];
}
```

Skip `Equatable` (and `props`) only for request body models (never compared for equality).

#### Rule 17 — Extend models with `super` constructor forwarding

```dart
class ChildModel extends ParentModel {
  final String extra;

  ChildModel({
    required this.extra,
    required super.id,      // forward to parent
    required super.name,
  });

  @override
  Map<String, dynamic> toJson() => super.toJson()..addAll({'extra': extra});

  factory ChildModel.fromJson(Map<String, dynamic> json) => ChildModel(
    extra: json['extra'] ?? '',
    id: json['id'] ?? 0,
    name: json['name'] ?? '',
  );
}
```

#### Rule 18 — Use `??` in `fromJson`, never `!`

```dart
// CORRECT
id: json['id'] ?? 0,
name: json['name'] ?? '',
items: (json['items'] as List?)?.map((e) => Item.fromJson(e)).toList() ?? [],

// WRONG — crashes on missing keys
id: json['id']!,
name: json['name']!,
```

Only use `!` when you have a prior `!= null` guard directly above.

---

### Cubits

#### Rule 19 — Cubit constructor order: `super(initial)` → inject dependencies → nothing else

```dart
// CORRECT
class MyFeatureCubit extends AsyncCubit<MyModel> {
  late final SomeOtherService _service;

  MyFeatureCubit() : super(MyModel.initial()) {
    _service = injector();   // only injection here
  }
}

// WRONG — business logic in constructor
MyFeatureCubit() : super(MyModel.initial()) {
  _service = injector();
  loadData();  // side effect — put this in an init() method instead
}
```

If you need to run logic on creation, expose an `init()` method and call it from the widget's `initState`.

#### Rule 20 — Never emit after the cubit is closed

```dart
// CORRECT — AsyncCubit already guards this
@override
void emit(AsyncState<T> state) {
  if (isClosed) return;
  super.emit(state);
}

// Also cancel subscriptions on close
@override
Future<void> close() async {
  await _streamSubscription?.cancel();
  return super.close();
}
```

#### Rule 21 — State updates use `copyWith`, never rebuild the full state object

```dart
// CORRECT
emit(state.copyWith(data: newList, status: BaseStatus.success));

// WRONG — loses other state fields
emit(AsyncState(status: BaseStatus.success, data: newList, msg: null));
```

---

### When to use a Cubit vs a Widget

#### Rule 22 — Use a Cubit ONLY when at least one of these is true

1. **The operation hits the network / local DB** (any `BaseCrudUseCase` call, socket event, cache read/write).
2. **Multiple screens or widgets need to react to the same state change** (shared state).

If neither condition is met, keep the logic in the widget itself.

```
Does it call an API or DB?       → Cubit
Does multiple screens depend on it? → Cubit
Otherwise                        → Widget (StatefulWidget or StatelessWidget)
```

---

#### Rule 23 — UI-only state lives in a StatefulWidget, not a Cubit

Toggle visibility, expand/collapse, tab index, form field values, animation controllers — these are local UI concerns. A Cubit for them adds unnecessary boilerplate and makes the code harder to follow.

```dart
// CORRECT — toggle is local to one widget
class _MyWidgetState extends State<MyWidget> {
  bool _isExpanded = false;

  void _toggle() => setState(() => _isExpanded = !_isExpanded);
}

// WRONG — a Cubit just to hold a bool no other screen cares about
class ExpandCubit extends Cubit<bool> {
  ExpandCubit() : super(false);
  void toggle() => emit(!state);
}
```

---

#### Rule 24 — Derived / computed values are getters on the widget or in the build method, not a Cubit

```dart
// CORRECT — computed from props already on the widget
class PriceWidget extends StatelessWidget {
  final int price;
  final int discount;

  double get finalPrice => price - (price * discount / 100);  // local getter

  @override
  Widget build(BuildContext context) {
    return Text(finalPrice.toCurrency());
  }
}

// WRONG — Cubit emitting a value that only this widget uses
class PriceCubit extends Cubit<double> {
  PriceCubit() : super(0);
  void compute(int price, int discount) => emit(price - (price * discount / 100));
}
```

---

#### Rule 25 — A StatelessWidget is the default; upgrade to StatefulWidget only when you need `setState`, `initState`, `dispose`, or a `TickerProvider`

```dart
// Use StatelessWidget when
// - widget only displays data passed as constructor params
// - no local mutable state is needed

// Upgrade to StatefulWidget when you need any of:
// - setState() for local UI state
// - initState() to run code once on mount (e.g. call cubit.loadData())
// - dispose() to cancel controllers, subscriptions
// - AnimationController / TickerProviderStateMixin
// - TextEditingController / FocusNode (they need dispose)
```

---

#### Rule 26 — Call `cubit.loadData()` from `initState`, not from the Cubit constructor

The Cubit constructor is for wiring dependencies only (Rule 19). Triggering an API call belongs to the widget lifecycle.

```dart
// CORRECT
class MyScreen extends StatefulWidget { ... }

class _MyScreenState extends State<MyScreen> {
  @override
  void initState() {
    super.initState();
    context.read<MyFeatureCubit>().loadData();
  }
}

// WRONG — side effect in Cubit constructor
MyFeatureCubit() : super(MyModel.initial()) {
  _service = injector();
  loadData();  // fires before the widget tree is ready
}
```

---

#### Rule 27 — Decision table (quick reference)

| Scenario | Use |
|---|---|
| API call (GET / POST / PUT / DELETE) | `AsyncCubit` |
| Shared state across 2+ screens | `Cubit` |
| Socket / real-time events | `Cubit` |
| Local DB read/write | `Cubit` |
| User auth state | `UserCubit` (singleton) |
| Form field text / focus | `StatefulWidget` + `TextEditingController` |
| Expand / collapse / toggle | `StatefulWidget` + `setState` |
| Tab / page index (single screen) | `StatefulWidget` + `setState` |
| Animation | `StatefulWidget` + `AnimationController` |
| Pure display, no logic | `StatelessWidget` |

---

### UI Building Rules

#### Rule 28 — Every screen is a composition of small named widgets — never one giant `build()`

A screen file contains only the top-level scaffold/layout. Extract every distinct section into its own widget class.

```dart
// CORRECT — screen is thin, each section is its own widget
class RegisterScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          RegisterHeader(),
          RegisterForm(),
          RegisterFooter(),
        ],
      ),
    );
  }
}

// WRONG — everything inline, build() becomes 200+ lines
class RegisterScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // 40 lines of header...
          // 80 lines of form...
          // 30 lines of footer...
        ],
      ),
    );
  }
}
```

---

#### Rule 29 — A child widget that selects or picks a value receives a callback — the parent owns the variable

The child handles the picking UI (button, bottom sheet, file picker). The **parent** holds the value and updates it via the callback. This keeps submit logic in one place.

```dart
// CORRECT — parent owns all values, passes callbacks down
class _RegisterScreenState extends State<RegisterScreen> {
  File? _image;
  String? _selectedCity;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ImagePickerWidget(
          image: _image,
          onImageSelected: (file) => setState(() => _image = file),
        ),
        CityPickerWidget(
          selectedCity: _selectedCity,
          onCitySelected: (city) => setState(() => _selectedCity = city),
        ),
        SubmitButton(
          onTap: () => context.read<RegisterCubit>().register(
            image: _image,
            city: _selectedCity,
          ),
        ),
      ],
    );
  }
}

// Child widget — only handles the picking UI, fires the callback
class ImagePickerWidget extends StatelessWidget {
  final File? image;
  final void Function(File file) onImageSelected;

  const ImagePickerWidget({
    required this.image,
    required this.onImageSelected,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () async {
        final file = await getImage();
        if (file != null) onImageSelected(file);
      },
      child: image != null ? Image.file(image!) : const Icon(Icons.add_a_photo),
    );
  }
}

// WRONG — child stores the value, parent can't read it on submit
class _ImagePickerWidgetState extends State<ImagePickerWidget> {
  File? _image;  // ← parent is blind to this
}
```

---

#### Rule 30 — Callback parameters follow the `onVerbNoun` naming convention

```dart
// CORRECT
final void Function(File file)    onImageSelected;
final void Function(String city)  onCitySelected;
final void Function(int index)    onTabChanged;
final void Function()             onSubmitPressed;
final void Function(bool value)   onToggleChanged;
final void Function(MyModel item) onItemDeleted;

// WRONG — vague or missing verb
final void Function(File)  imageCallback;
final Function             onChange;
final void Function()      submit;
```

---

#### Rule 31 — Pass only the fields the child actually uses, not the whole model

```dart
// CORRECT — child receives exactly what it needs
class UserCardWidget extends StatelessWidget {
  final String name;
  final String avatarUrl;
  final void Function() onTap;
  ...
}

// ACCEPTABLE — when the child genuinely uses 5+ fields from a stable model
class UserCardWidget extends StatelessWidget {
  final UserModel user;
  ...
}

// WRONG — passing full model when only name + avatar are used
class AvatarWidget extends StatelessWidget {
  final UserModel user;   // only uses user.avatarUrl
}
```

---

#### Rule 32 — A display-only widget is `StatelessWidget`; upgrade to `StatefulWidget` only when needed

```dart
// StatelessWidget — pure display, data passed via constructor
class PackagePriceTag extends StatelessWidget { ... }
class ChatBubble extends StatelessWidget { ... }
class SectionTitle extends StatelessWidget { ... }

// Upgrade to StatefulWidget only when you need:
// - setState() for local UI state (toggle, expand)
// - initState() / dispose() for controllers or subscriptions
// - AnimationController / TickerProviderStateMixin
// - TextEditingController / FocusNode (must be disposed)
```

---

#### Rule 33 — `TextEditingController` and `FocusNode` live in the parent `StatefulWidget` that submits — disposed in `dispose()`

```dart
class _LoginScreenState extends State<LoginScreen> {
  late final TextEditingController _phoneController;
  late final FocusNode _phoneFocus;

  @override
  void initState() {
    super.initState();
    _phoneController = TextEditingController();
    _phoneFocus = FocusNode();
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _phoneFocus.dispose();
    super.dispose();
  }
}
```

Never create a controller inside `build()` — it gets recreated on every rebuild and leaks memory.

---

#### Rule 34 — Repeated visual structures are extracted into a shared widget, not copy-pasted

If the same structure appears in 2+ places, extract it once into `widgets/` (feature-level) or `core/widgets/` (cross-feature).

```dart
// CORRECT — defined once, used everywhere
class LabeledTextField extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final String? Function(String?)? validator;
  ...
}

LabeledTextField(label: LocaleKeys.name,  controller: _nameController)
LabeledTextField(label: LocaleKeys.email, controller: _emailController)

// WRONG — same Column+Text+TextFormField block pasted 5 times
```

---

#### Rule 35 — Screen folder structure

```
features/
  my_feature/
    presentation/
      screens/
        my_feature_screen.dart          ← scaffold + layout only
      widgets/
        my_feature_header.dart          ← extracted header section
        my_feature_form.dart            ← extracted form section
        my_feature_image_picker.dart    ← extracted picker widget
      cubits/
        my_feature_cubit.dart
```

The screen file imports from `widgets/`. Widgets do not import the screen file.

---

## Translations

### Source of truth — `assets/translations/lang.json`

This is the **only file you ever edit** for translations. Never touch the generated files.

Generated files (do not edit manually):
- `assets/translations/en.json` — English locale
- `assets/translations/ar.json` — Arabic locale
- `lib/src/config/language/locale_keys.g.dart` — Dart constants

After editing `lang.json`, regenerate everything with:
```
make translations
# or directly:
dart run generate/strings/main.dart
```

---

### Key format in `lang.json`

Two formats are supported:

**Format 1 — Plain English key** (key derived from the text itself):
```json
"English Text Here": "النص بالعربي"
```
→ Generates `LocaleKeys.englishTextHere` in Dart (text converted to camelCase)

**Format 2 — Explicit camelCase key with `#$` separator** (preferred when key differs from display text):
```json
"camelCaseKey #$ English Display Text": "النص بالعربي"
```
→ Generates `LocaleKeys.camelCaseKey` in Dart. The part before `#$` becomes the key; the part after becomes the English display value.

**Section dividers** (for organizing the file — ignored by generator):
```json
"_____________________________________SectionName___________________________________": ""
```

---

### Adding a new string

1. Open `assets/translations/lang.json`
2. Add the entry using the appropriate format:
   ```json
   "myNewKey #$ My New Label": "تسمية جديدة"
   ```
3. Run `make translations` to regenerate
4. Use `LocaleKeys.myNewKey` in Dart

**Never** hardcode display strings — always go through `LocaleKeys.*`.

---

### Examples from the existing file

| `lang.json` key | Dart usage |
|---|---|
| `"name #$ Name"` | `LocaleKeys.name` |
| `"fillField #$ This field is required"` | `LocaleKeys.fillField` |
| `"pleaseEnterIdentityNumber #$ Please enter identity number"` | `LocaleKeys.pleaseEnterIdentityNumber` |
| `"Are you smoke"` | `LocaleKeys.areYouSmoke` |
| `"City"` | `LocaleKeys.city` |

---

### Rule 36 — Always add new strings to `lang.json`, never hardcode

```dart
// CORRECT
AppText(LocaleKeys.confirmCode)

// WRONG — hardcoded string
AppText('Confirm Code')
AppText('كود التأكيد')
```

---

## Makefile

The project `Makefile` at the repo root contains all recurring dev commands. Run targets with `make <target>`.

### Existing targets

| Target | What it does |
|---|---|
| `make clean` | `flutter clean && flutter pub get` |
| `make run` | `flutter run` |
| `make apk` | Build APK split per ABI |
| `make ios` | Build iOS |
| `make upgrade` | `flutter pub upgrade` |
| `make handlePods` | `cd ios && pod install && pod update` |
| `make openXcode` | Open `ios/Runner.xcworkspace` |
| `make translations` | Regenerate locale keys from `lang.json` |
| `make gradleFix` | Stop Gradle daemons, kill Java processes, remove lock files |
| `make clearGradleCache` | Remove `android/.gradle` and `~/.gradle/caches` |
| `make buildIos` | Run `upload_ios.sh` |
| `make distribute ARGS=...` | Distribute iOS via `distribute_ios.sh` |
| `make distributeAndroid ARGS=...` | Distribute Android via `distribute_android.sh` |

---

### Rule 37 — Add new useful commands to the Makefile automatically

When you discover or use a terminal command that:
- Fixes a recurring build/tooling problem (Gradle, CocoaPods, Xcode, pub cache, etc.)
- Generates code or assets
- Automates a multi-step dev workflow

→ **Add it to `Makefile` immediately** without waiting to be asked. Use a short `.PHONY` target name, a one-line `##` comment describing it, and group it near related targets.

```makefile
# Clean pub cache (fixes corrupt package downloads)
clearPubCache:
	flutter pub cache repair
```

Do **not** add one-off commands, commands that require interactive input, or commands specific to a single dev's machine.


---

## Feature Structure Pattern — Follow Sign Up

The sign-up feature in `/Users/aaita/Desktop/apps/sitr/lib/src/features/auth` is the reference structure for future features. When adding any feature, mirror its organization, naming style, and separation of responsibilities unless there is a strong reason not to.

### Rule 38 — Organize each feature like sign up

Use this structure for new features:

```text
features/feature_name/
  imports.dart
  data/
    enums/
    models/
  presentation/
    cubits/
    screens/
    widgets/
      shared/
      feature_name/
```

Keep request/response/body models in `models/`. Keep UI, cubits, feature data helpers, enums, screens, and widgets under `presentation/`. Split widgets by responsibility: reusable widgets in `widgets/shared/`, feature-specific widgets in `widgets/feature_name/`, and flow-specific subfolders when needed.

### Rule 39 — Use a feature barrel when the feature has many files

For larger features, create `imports.dart` at the feature root. Put common imports there and register screens/widgets as `part` files, matching sign up:

```dart
// screen file
part of '../../imports.dart';

// widget file under presentation/widgets/feature_name
part of '../../../imports.dart';
```

Do not scatter duplicated imports across every file when a feature-level barrel already exists.

### Rule 40 — Screens orchestrate, widgets own form details

A feature screen should own only the flow-level state and orchestration:
- `GlobalKey<FormState>`
- selected mode/type notifiers
- `BlocProvider` setup
- scaffold composition
- submit button behavior
- success navigation

Do not put field controllers, per-field mutation, or conditional form sections directly in the screen. Follow `SignUpScreen` + `SignUpFields`: the screen validates and submits; the fields widget owns controllers, initializes/disposes them, updates the body with `copyWith`, and sends the latest body upward through a callback.

### Rule 41 — Use body models for form submission

Feature forms should submit typed body models, not loose maps from the UI. Follow `SignUpBody`, `MaleAndFemaleSignUp`, and `ParentSignUp`:
- Base body model contains shared fields
- Specialized child body models extend the base body for mode-specific fields
- Every body model provides `initial()`, `copyWith(...)`, and `toJson()`
- Child `toJson()` calls `super.toJson()..addAll({...})`

Build request maps only inside `toJson()`. UI code should update models with `copyWith`, not construct raw request maps.

### Rule 42 — Cubits execute use cases/API calls only

Feature cubits should extend `AsyncCubit` when they load or submit remote data. Keep them thin, like `SignUpCubit`:

```dart
Future<void> submit(
  FeatureBody body, {
  required void Function(BaseModel data) onSuccess,
}) async {
  await executeAsyncWithBaseModel(
    operation: () => baseCrudUseCase.call(CrudBaseParmas(
      api: ApiConstants.someEndpoint,
      httpRequestType: HttpRequestType.post,
      body: body.toJson(),
    )),
    onSuccess: (data) => onSuccess(data),
  );
}
```

Always `await` `executeAsyncWithBaseModel`. Put navigation and UI messages in the screen callback, not inside the cubit.

### Rule 43 — Type-specific UI uses enums and extension checks

When a feature has multiple modes, use enums plus `is*` extension getters, as sign up does with `UserType` and `UserGender`. Use `ValueNotifier`, `ValueListenableBuilder`, `Visibility`, or `if (...) ...[]` to switch visible form sections. Avoid string comparisons and duplicated screens for simple mode differences.

### Rule 44 — Follow sign-up submission flow

For form features, use this flow:
1. User updates fields; field widget updates a typed body with `copyWith`.
2. Screen validates `formKey.currentState`.
3. Screen calls the feature cubit and awaits it.
4. Cubit submits `body.toJson()` through `baseCrudUseCase` / `CrudBaseParmas`.
5. Screen handles success: show `MessageUtils`, navigate with `Go`, and trigger analytics or follow-up flow if needed.

Do not bypass validation, do not navigate from cubits, and do not hardcode display strings outside `LocaleKeys`.

### Rule 45 — Screen build skill

Use this workflow when building or refactoring any Sokoun screen from Figma:

1. Read the Figma node with `get_design_context` when a Figma URL is provided. Use metadata only as orientation; full design context is the source of truth when available.
2. Inspect `apps/sokoun_app/lib/shared_widgets` and feature-local widgets before creating new UI. Reuse existing controls whenever they match the design.
3. Put the screen under its feature's `screens/` folder and name the public widget by the screen role only, for example `LoginScreen`. Do not prefix screen classes with the app name.
4. Put screen-specific presentational widgets under `screens/widgets/<screen_name>/`, for example `screens/widgets/login/LoginHeader` and `LoginDivider`.
5. Keep the screen responsible for flow-level orchestration only: form key, controllers or callbacks, submit handling, and screen layout. Move reusable visual chunks into widgets.
6. Use `LocaleKeys` for every user-facing string. If keys are missing, add translations through the repo localization flow and keep generated keys in sync.
7. Reuse `packages/core` UI primitives (`AppText`, `DefaultButton`) and narrow extension imports such as `sized_box_helper.dart` for spacing.
8. If a shared widget blocks correct behavior, extend it with optional parameters instead of duplicating its styling. Preserve existing defaults for other call sites.
9. Wire the screen into `MaterialApp.home` only when the task requires making it immediately visible.
10. Run `dart format`, `flutter analyze apps/sokoun_app`, and `flutter test apps/sokoun_app` after the refactor.
