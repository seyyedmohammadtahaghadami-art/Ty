from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['ok'] is True
    assert r.json()['version'] == '5.0.0'

def test_reject_bad_extension():
    r = client.post('/api/convert', files={'file': ('test.txt', b'hello', 'text/plain')})
    assert r.status_code == 400
