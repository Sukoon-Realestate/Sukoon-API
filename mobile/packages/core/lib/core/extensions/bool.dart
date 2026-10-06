import '../../config/language/locale_keys.g.dart';

extension ConvertToLocaleKeys on bool{
  String? toNormalLang(){
    if(this){
      return LocaleKeys.yes;

    }else if(!this){
      return LocaleKeys.no;

    }

    return null;
  }
}