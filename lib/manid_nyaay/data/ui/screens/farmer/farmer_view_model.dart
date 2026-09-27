import 'package:flutter/foundation.dart';
import 'package:sih2631/manid_nyaay/data/domain/model/farmer.dart';
import 'package:sih2631/manid_nyaay/data/domain/repository/sync_repository.dart';
import 'package:sih2631/manid_nyaay/data/fixture/repository.dart';
// Import your repository and domain model
// import 'package:mandi_nyaay/data/fixture/fixture_farmer_repository.dart';
// import 'package:mandi_nyaay/domain/model/farmer.dart';
// import 'package:mandi_nyaay/domain/repository/farmer_repository.dart';

class FarmerViewModel extends ChangeNotifier {
  final String farmerId;
  final FarmerRepository _repository;

  Farmer? _farmer;
  Farmer? get farmer => _farmer;

  bool _isLoading = true;
  bool get isLoading => _isLoading;

  FarmerViewModel({
    required this.farmerId,
    FarmerRepository? repository,
  }) : _repository = repository?? FixtureFarmerRepository() {
    _loadFarmer();
  }

  Future<void> _loadFarmer() async {
    _isLoading = true;
    notifyListeners();

    _farmer = await _repository.getFarmerById(farmerId);

    _isLoading = false;
    notifyListeners();
  }
}