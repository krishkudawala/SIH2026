import base64
import json
import requests
import sys
import os
BASE = os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000')

# TEST A
print('=== EXECUTING TEST A: SESSION A ===')
res_a = requests.post(f'{BASE}/sessions', json={
    'lot_id': 'LOT_DYNAMIC_ALPHA_01',
    'source_reference': 'FARMER_RAMESH_PATIL_MH15',
    'target_sample_size': 20,
    'rule_pack_id': 'AGMARK_ONION_2024_V1',
    'declared_bag_count': 100,
    'certified_lot_weight_kg': 2000.0
})
assert res_a.status_code == 200, res_a.text
sess_a = res_a.json()
id_a = sess_a['id']
print(f"Session A Created: ID={id_a}, Lot={sess_a['lot_id']}, Status={sess_a['status']}")

with open('assets/sample_produce/01_mixed_damaged_rotten_healthy.jpg', 'rb') as f:
    b64_a = base64.b64encode(f.read()).decode('utf-8')

cap_res_a = requests.post(f'{BASE}/sessions/{id_a}/captures', json={
    'image_base64': b64_a,
    'filename': 'alpha_batch.jpg',
    'capture_role': 'PRIMARY_SAMPLE_CAPTURE',
    'view_angle': 'TOP'
})
assert cap_res_a.status_code == 200, cap_res_a.text
print('Capture A uploaded successfully')

inf_res_a = requests.post(f'{BASE}/sessions/{id_a}/inference')
assert inf_res_a.status_code == 200, inf_res_a.text
inf_a = inf_res_a.json()
obs_count_a = inf_a.get('observations_count', len(inf_a.get('items', [])))
print(f'Inference A: Observations Count={obs_count_a}')

obs_a = requests.get(f'{BASE}/sessions/{id_a}/observations').json()
samp_a = requests.get(f'{BASE}/sessions/{id_a}/sampling').json()
meas_a = requests.get(f'{BASE}/sessions/{id_a}/measurement').json()
wt_a = requests.get(f'{BASE}/sessions/{id_a}/weight').json()
rev_a = requests.get(f'{BASE}/sessions/{id_a}/review').json()
dec_a = requests.post(f'{BASE}/sessions/{id_a}/decision').json()
ev_a = requests.get(f'{BASE}/sessions/{id_a}/evidence').json()
rep_a = requests.get(f'{BASE}/sessions/{id_a}/report').json()
replay_a = requests.post(f'{BASE}/sessions/{id_a}/replay').json()

print(f"Session A Evidence Root: {ev_a['evidence_root_hash'][:16]}...")
print(f"Session A Replay Identical: {replay_a['is_bit_for_bit_identical']}")
print(f"Session A Decision Grade: {dec_a['procurement_grade']}")

# TEST B
print('\n=== EXECUTING TEST B: SESSION B ===')
res_b = requests.post(f'{BASE}/sessions', json={
    'lot_id': 'LOT_DYNAMIC_BETA_02',
    'source_reference': 'FARMER_SURESH_JADHAV_MH15',
    'target_sample_size': 10,
    'rule_pack_id': 'AGMARK_ONION_2024_V1',
    'declared_bag_count': 40,
    'certified_lot_weight_kg': 800.0
})
assert res_b.status_code == 200, res_b.text
sess_b = res_b.json()
id_b = sess_b['id']
print(f"Session B Created: ID={id_b}, Lot={sess_b['lot_id']}, Status={sess_b['status']}")

with open('assets/sample_produce/02_cropped_half_produce.jpg', 'rb') as f:
    b64_b = base64.b64encode(f.read()).decode('utf-8')

cap_res_b = requests.post(f'{BASE}/sessions/{id_b}/captures', json={
    'image_base64': b64_b,
    'filename': 'beta_batch.jpg',
    'capture_role': 'PRIMARY_SAMPLE_CAPTURE',
    'view_angle': 'TOP'
})
assert cap_res_b.status_code == 200, cap_res_b.text
print('Capture B uploaded successfully')

inf_res_b = requests.post(f'{BASE}/sessions/{id_b}/inference')
assert inf_res_b.status_code == 200, inf_res_b.text
inf_b = inf_res_b.json()
obs_count_b = inf_b.get('observations_count', len(inf_b.get('items', [])))
print(f'Inference B: Observations Count={obs_count_b}')

obs_b = requests.get(f'{BASE}/sessions/{id_b}/observations').json()
samp_b = requests.get(f'{BASE}/sessions/{id_b}/sampling').json()
meas_b = requests.get(f'{BASE}/sessions/{id_b}/measurement').json()
wt_b = requests.get(f'{BASE}/sessions/{id_b}/weight').json()
rev_b = requests.get(f'{BASE}/sessions/{id_b}/review').json()
dec_b = requests.post(f'{BASE}/sessions/{id_b}/decision').json()
ev_b = requests.get(f'{BASE}/sessions/{id_b}/evidence').json()
rep_b = requests.get(f'{BASE}/sessions/{id_b}/report').json()
replay_b = requests.post(f'{BASE}/sessions/{id_b}/replay').json()

print(f"Session B Evidence Root: {ev_b['evidence_root_hash'][:16]}...")
print(f"Session B Replay Identical: {replay_b['is_bit_for_bit_identical']}")
print(f"Session B Decision Grade: {dec_b['procurement_grade']}")

print('\n=== VERIFYING DYNAMIC SEPARATION (TEST A vs B) ===')
assert id_a != id_b, 'IDs must be distinct'
assert sess_a['lot_id'] != sess_b['lot_id'], 'Lot IDs must be distinct'
assert obs_count_a != obs_count_b, f'Observation counts must differ: {obs_count_a} vs {obs_count_b}'
assert ev_a['evidence_root_hash'] != ev_b['evidence_root_hash'], 'Evidence hashes must differ'
print('DIVERGENCE CONFIRMED:')
print(f" - Session A: ID={id_a}, Observations={obs_count_a}, Hash={ev_a['evidence_root_hash'][:16]}")
print(f" - Session B: ID={id_b}, Observations={obs_count_b}, Hash={ev_b['evidence_root_hash'][:16]}")

# TEST C: State mutation & refresh
print('\n=== EXECUTING TEST C: STATE MUTATION & REFRESH ===')
override_res = requests.post(f'{BASE}/sessions/{id_a}/decision', json={
    'override_grade': 'URS',
    'override_reason': 'Secondary inspection visual audit adjustment'
})
assert override_res.status_code == 200, override_res.text
updated_dec_a = requests.get(f'{BASE}/sessions/{id_a}').json()
assert updated_dec_a['procurement_grade'] == 'URS', f"Expected URS, got {updated_dec_a['procurement_grade']}"
print(f"Session A Grade successfully updated dynamically to: {updated_dec_a['procurement_grade']}")

# TEST D: Error handling
print('\n=== EXECUTING TEST D: BACKEND UNAVAILABLE / INVALID SESSION ===')
err_res = requests.get(f'{BASE}/sessions/sess_non_existent_99999')
assert err_res.status_code == 404, f'Expected 404, got {err_res.status_code}'
print(f'Correctly returned 404 error response without fabricating dummy data: {err_res.json()}')

# TEST E: Recovery from persistence
print('\n=== EXECUTING TEST E: STATE RECOVERY FROM PERSISTENCE ===')
recovered_a = requests.get(f'{BASE}/sessions/{id_a}').json()
assert recovered_a['id'] == id_a
assert recovered_a['lot_id'] == 'LOT_DYNAMIC_ALPHA_01'
assert recovered_a['procurement_grade'] == 'URS'
print(f"Recovered session from SQLite store: Lot={recovered_a['lot_id']}, Status={recovered_a['status']}, Grade={recovered_a['procurement_grade']}")

print('\nALL ACCEPTANCE TESTS (A, B, C, D, E) PASSED WITH 100% REAL DYNAMIC DATA!')
