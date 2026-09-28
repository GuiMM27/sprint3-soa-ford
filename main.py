from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
import datetime

# Configurações JWT
SECRET_KEY = "ford_challenge_secret_key"
ALGORITHM = "HS256"

app = FastAPI(
    title="API Ford VIN Share",
    description="API para gestão de pós-venda e leads preditivos",
    version="1.0.0"
)

# --- TRATAMENTO DE ERROS PADRONIZADO ---
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"erro": exc.detail, "codigo": exc.status_code},
    )

# --- MOCK DE DADOS (Simulando Banco de Dados) ---
USUARIOS = {
    "cliente1": {"senha": "123", "role": "cliente", "id": 1},
    "admin1": {"senha": "admin", "role": "concessionaria", "id": 99}
}
VEICULOS = {
    "VIN123": {"modelo": "Ranger", "ano": 2022, "status_servico": "Pendente"}
}

# --- MODELOS DE DADOS ---
class LoginRequest(BaseModel):
    usuario: str
    senha: str

class LeadCreate(BaseModel):
    chassi: str
    probabilidade_churn: float

# --- AUTENTICAÇÃO E AUTORIZAÇÃO (JWT) ---
def criar_token(dados: dict):
    dados_copia = dados.copy()
    expiracao = datetime.datetime.utcnow() + datetime.timedelta(hours=2) # Expiração
    dados_copia.update({"exp": expiracao})
    return jwt.encode(dados_copia, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Dependência para proteger rotas
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def obter_usuario_logado(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return verificar_token(credentials.credentials)

# --- ENDPOINTS (MATURIDADE REST NÍVEL 2) ---

@app.post("/api/auth/login", status_code=200, summary="Endpoint Público de Login")
def login(req: LoginRequest):
    """Gera o token JWT para usuários válidos[cite: 6]."""
    user = USUARIOS.get(req.usuario)
    if not user or user["senha"] != req.senha:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = criar_token({"sub": req.usuario, "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/veiculos/{chassi}", status_code=200, summary="Busca histórico do veículo")
def obter_veiculo(chassi: str, usuario: dict = Depends(obter_usuario_logado)):
    """Rota protegida orientada a recursos utilizando método HTTP adequado[cite: 6]."""
    veiculo = VEICULOS.get(chassi)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return veiculo

@app.post("/api/leads", status_code=201, summary="Cadastra um novo lead preditivo")
def criar_lead(lead: LeadCreate, usuario: dict = Depends(obter_usuario_logado)):
    """Criação de recurso com status code 201 Created e controle de acesso por perfil[cite: 6]."""
    if usuario.get("role") != "concessionaria":
        raise HTTPException(status_code=403, detail="Acesso negado: Requer perfil de concessionária")
    
    return {"mensagem": "Lead cadastrado com sucesso", "dados": lead}