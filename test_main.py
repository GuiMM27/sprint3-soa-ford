from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_sucesso():
    """Cenário de Sucesso: Login válido retorna 200 e JWT[cite: 6]"""
    response = client.post("/api/auth/login", json={"usuario": "cliente1", "senha": "123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_acesso_nao_autorizado():
    """Cenário de Acesso Não Autorizado: Tentar acessar sem token[cite: 6]"""
    response = client.get("/api/veiculos/VIN123")
    assert response.status_code == 403 # O HTTPBearer bloqueia automaticamente a falta de token

def test_veiculo_nao_encontrado():
    """Cenário de Erro: Token válido, mas recurso não existe (404)[cite: 6]"""
    # 1. Faz login para pegar token
    login_res = client.post("/api/auth/login", json={"usuario": "cliente1", "senha": "123"})
    token = login_res.json()["access_token"]
    
    # 2. Usa o token para buscar chassi inexistente
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/veiculos/CHASSIFALSO", headers=headers)
    
    assert response.status_code == 404
    assert response.json() == {"erro": "Veículo não encontrado", "codigo": 404}