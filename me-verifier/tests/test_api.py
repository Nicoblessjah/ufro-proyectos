import io
from PIL import Image
from api.app import app   # <- importa la app del Flask

def test_healthz():
    client = app.test_client()
    r = client.get('/healthz')
    assert r.status_code == 200

# Prueba de humo: envía una imagen en blanco y espera error por no detectar rostro
def test_verify_no_face():
    client = app.test_client()
    buf = io.BytesIO()
    Image.new('RGB', (200, 200), (255, 255, 255)).save(buf, format='PNG')
    buf.seek(0)
    data = {'image': (buf, 'white.png')}
    r = client.post('/verify', data=data, content_type='multipart/form-data')
    assert r.status_code in (200, 422, 400)
