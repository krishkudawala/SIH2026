import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/lot.dart';
import 'package:sih2631/manid_nyaay/data/fixture/lot_repository.dart';
// Import your repositories and models
// import 'package:mandi_nyaay/data/fixture/fixture_lot_repository.dart';
// import 'package:mandi_nyaay/domain/model/lot.dart';

class LotDetailsViewModel extends ChangeNotifier {
  final String lotId;
  final FixtureLotRepository _repository = FixtureLotRepository();

  Lot? _lot;
  Lot? get lot => _lot;

  bool _isLoading = true;
  bool get isLoading => _isLoading;

  LotDetailsViewModel({required this.lotId}) {
    _fetchLot();
  }

  Future<void> _fetchLot() async {
    _isLoading = true;
    notifyListeners();

    _lot = (await _repository.getLotById(lotId)) as Lot?;

    _isLoading = false;
    notifyListeners();
  }
}