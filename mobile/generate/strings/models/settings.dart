import 'dart:io';

class Settings{
  File? file;
  int mode;

  Settings({
    this.file,
    required this.mode,
  });

  factory Settings.fromJson({required Map<String, dynamic> json, required File file}){
    int mode = 0;

    //modifyMode
    if(json['mode'] != null){
      mode = json['mode'];
    }

    return Settings(
      file: file,
      mode: mode,
    );
  }

  Map<String, dynamic> toJson(){
    final Map<String, dynamic> map = <String, dynamic>{};
    map.putIfAbsent('mode', () => mode);
    return map;
  }
}