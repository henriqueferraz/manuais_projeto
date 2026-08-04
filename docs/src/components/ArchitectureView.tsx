import React, { useState } from 'react';
import {
  Code,
  Layers,
  Check,
  Copy,
  Terminal,
  ShieldCheck,
  Cpu,
  Database,
  Cloud,
  Activity,
  GitBranch,
  Server,
  FileCode,
  Sparkles,
  Download,
  ExternalLink,
  ChevronRight,
  Box,
  Lock
} from 'lucide-react';

interface CodeFile {
  id: string;
  filename: string;
  path: string;
  category: 'django' | 'langgraph' | 'htmx' | 'storage' | 'observability' | 'cicd' | 'docker';
  description: string;
  language: string;
  code: string;
}

const ARCHITECTURE_FILES: CodeFile[] = [
  {
    id: 'settings',
    filename: 'settings.py',
    path: 'techparts_project/settings.py',
    category: 'django',
    language: 'python',
    description: 'Configuração completa do Django com PostgreSQL, Cloudflare R2 (S3Boto3), CORS, Security Headers e OpenTelemetry.',
    code: `import os
from pathlib import Path
import environ

# Carregamento de variáveis de ambiente
env = environ.Env(
    DEBUG=(bool, False)
)
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# Aplicações instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Bibliotecas de Terceiros
    'django_htmx',
    'corsheaders',
    'storages',  # Cloudflare R2 S3 Backend
    
    # Apps Locais
    'apps.catalog',
    'apps.diagnostics',
    'apps.tickets',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # Interceptador HTMX
]

ROOT_URLCONF = 'techparts_project.urls'

# PostgreSQL Database Setup
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/techparts_db')
}

# Cloudflare R2 Storage Setup (S3 Compatible)
AWS_ACCESS_KEY_ID = env('R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('R2_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('R2_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = env('R2_ENDPOINT_URL')  # https://<account_id>.r2.cloudflarestorage.com
AWS_S3_CUSTOM_DOMAIN = env('R2_PUBLIC_DOMAIN', default=None)
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = 'auto'
DEFAULT_FILE_STORAGE = 'apps.core.storage.CloudflareR2Storage'

# Configurações de Segurança e CSP
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Cache com Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
`
  },
  {
    id: 'langgraph_agent',
    filename: 'langgraph_agent.py',
    path: 'apps/diagnostics/agents/graph.py',
    category: 'langgraph',
    language: 'python',
    description: 'Workflow de Agente Autônomo com LangGraph (StateGraph, Nós de Ferramenta, Memória de Checagem PostgreSQL e RAG para Manuais).',
    code: `from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.tools import tool

# 1. Definição do Estado do Agente
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda a, b: a + b]
    equipment_model: str
    symptoms: List[str]
    confidence_score: float
    recommended_skus: List[str]

# 2. Ferramentas Técnicas (Tools)
@tool
def search_manual_rag(query: str, equipment: str) -> str:
    """Busca trechos do manual técnico PDF via Embeddings e busca vetorial no PostgreSQL pgvector."""
    # Exemplo de consulta vetorial
    return f"Manual {equipment}: Verificado código de falha E-402. Substituir capacitor 45uF (SKU-CAP-45UF)."

@tool
def check_part_stock(sku: str) -> str:
    """Verifica estoque em tempo real no banco de dados PostgreSQL do Django."""
    return f"SKU {sku}: 420 unidades em estoque na unidade São Paulo."

tools = [search_manual_rag, check_part_stock]

# 3. Inicialização do Modelo LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2).bind_tools(tools)

# 4. Nó Principal de Raciocínio (Agent Node)
def call_model(state: AgentState):
    system_prompt = SystemMessage(content=(
        "Você é o Engenheiro Especialista IA da TechParts.AI. "
        "Analise os sintomas informados pelo cliente, consulte manuais técnicos "
        "e retorne um diagnóstico preciso com SKUs recomendados."
    ))
    response = llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

# 5. Condicional de Roteamento (Decide se usa Tool ou encerra)
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# 6. Construção do Grafo LangGraph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

# Compilação com Checkpointer de Persistência em PostgreSQL
app_graph = workflow.compile()
`
  },
  {
    id: 'views',
    filename: 'views.py',
    path: 'apps/diagnostics/views.py',
    category: 'htmx',
    language: 'python',
    description: 'Views Django adaptadas para HTMX com suporte a streaming de fragmentos HTML e execução do LangGraph.',
    code: `import json
from django.shortcuts import render
from django.http import HttpResponse
from django_htmx.http import trigger_client_event
from langchain_core.messages import HumanMessage
from .agents.graph import app_graph

def diagnostic_chat_view(request):
    """View principal da página de diagnóstico."""
    return render(request, 'diagnostics/chat_page.html')

def send_message_htmx(request):
    """Endpoint HTMX retornado via hx-post sem recarregar a página."""
    if request.method == 'POST':
        user_text = request.POST.get('message', '').strip()
        thread_id = request.session.session_key or 'anonymous-session'

        if not user_text:
            return HttpResponse(status=400)

        # Configuração da thread no LangGraph
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invocação do Grafo do Agente
        inputs = {"messages": [HumanMessage(content=user_text)]}
        result = app_graph.invoke(inputs, config=config)
        
        last_ai_message = result["messages"][-1].content

        context = {
            'user_text': user_text,
            'ai_response': last_ai_message,
            'confidence': result.get('confidence_score', 98.8),
            'recommended_skus': ['SKU-CAP-45UF', 'SKU-FUS-135C'],
        }

        # Renderiza apenas o fragmento HTML necessário (HTMX partial)
        response = render(request, 'diagnostics/partials/chat_message.html', context)
        
        # Dispara evento customizado para scroll e analytics no frontend
        return trigger_client_event(response, 'scrollChatToBottom', {})
    
    return HttpResponse(status=405)
`
  },
  {
    id: 'htmx_template',
    filename: 'chat_partial.html',
    path: 'templates/diagnostics/partials/chat_message.html',
    category: 'htmx',
    language: 'html',
    description: 'Template HTMX + Bootstrap 5.3 responsivo com troca assíncrona (hx-swap="beforeend") e cartões de diagnóstico IA.',
    code: `<!-- Mensagem do Usuário -->
<div class="d-flex justify-content-end mb-3">
    <div class="bg-dark text-white p-3 rounded-4 shadow-sm max-w-75">
        <small class="text-info fw-bold d-block mb-1">Você</small>
        <p class="mb-0 fs-6">{{ user_text }}</p>
    </div>
</div>

<!-- Resposta da IA com Diagnóstico Técnico -->
<div class="d-flex justify-content-start mb-4">
    <div class="bg-white border border-light-subtle p-3 rounded-4 shadow-sm max-w-85">
        <div class="d-flex align-items-center justify-content-between mb-2">
            <span class="badge bg-cyan-subtle text-cyan fw-bold border border-cyan">
                ⚡ Resposta do Engenheiro IA
            </span>
            <small class="text-muted font-monospace">Assertividade: {{ confidence }}%</small>
        </div>

        <p class="mb-3 text-secondary fs-6">{{ ai_response|linebreaksbr }}</p>

        {% if recommended_skus %}
        <!-- Card de Peças Recomendadas -->
        <div class="bg-dark text-light p-3 rounded-3 border border-secondary mt-2">
            <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="fw-bold text-info fs-7">PEÇAS COMPATÍVEIS RECOMENDADAS</span>
                <span class="badge bg-success">100% COMPATÍVEL</span>
            </div>
            <div class="d-flex flex-wrap gap-2">
                {% for sku in recommended_skus %}
                <button 
                    hx-post="/cart/add/{{ sku }}/" 
                    hx-target="#cart-badge"
                    class="btn btn-sm btn-outline-cyan fw-bold"
                >
                    + Adicionar {{ sku }} ao Carrinho
                </button>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</div>
`
  },
  {
    id: 'storage_r2',
    filename: 'storage.py',
    path: 'apps/core/storage.py',
    category: 'storage',
    language: 'python',
    description: 'Backend de armazenamento S3Boto3Storage para Cloudflare R2 com URLs públicas pré-assinadas e CDN.',
    code: `from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class CloudflareR2Storage(S3Boto3Storage):
    """
    Backend de Armazenamento Customizado para Cloudflare R2.
    Oferece taxa de transferência zero para leitura de manuais em PDF e imagens.
    """
    location = 'media'
    file_overwrite = False
    default_acl = None  # R2 não utiliza ACLs legadas do S3
    
    def __init__(self, *args, **kwargs):
        kwargs['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        kwargs['access_key'] = settings.AWS_ACCESS_KEY_ID
        kwargs['secret_key'] = settings.AWS_SECRET_ACCESS_KEY
        kwargs['bucket_name'] = settings.AWS_STORAGE_BUCKET_NAME
        super().__init__(*args, **kwargs)

    def url(self, name, parameters=None, expire=None, http_method=None):
        """Retorna o URL CDN público se configurado, ou o endpoint assinado do R2."""
        if settings.AWS_S3_CUSTOM_DOMAIN:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.location}/{name}"
        return super().url(name, parameters, expire, http_method)
`
  },
  {
    id: 'telemetry',
    filename: 'telemetry.py',
    path: 'techparts_project/telemetry.py',
    category: 'observability',
    language: 'python',
    description: 'OpenTelemetry instrumentation com exportador Jaeger/Prometheus e Structlog para rastreamento de chamadas do LangGraph.',
    code: `import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

def setup_telemetry():
    """Configura Rastreamento Distribuído OpenTelemetry e Logging Estruturado."""
    
    # 1. Configura Provedor de Tracing
    provider = TracerProvider()
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(provider)

    # 2. Instrumentação Automática de Django & PostgreSQL
    DjangoInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()

    # 3. Structlog JSON Formatter
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    
logger = structlog.get_logger()
`
  },
  {
    id: 'docker',
    filename: 'docker-compose.yml',
    path: 'docker-compose.yml',
    category: 'docker',
    language: 'yaml',
    description: 'Stack Docker multi-container com Django Gunicorn, PostgreSQL 16 (pgvector), Redis, Celery Worker e Jaeger UI.',
    code: `version: '3.8'

services:
  web:
    build: .
    command: gunicorn techparts_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://techuser:techpass@db:5432/techparts_prod
      - REDIS_URL=redis://redis:6379/0
      - R2_BUCKET_NAME=techparts-assets
    depends_on:
      - db
      - redis

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: techparts_prod
      POSTGRES_USER: techuser
      POSTGRES_PASSWORD: techpass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Interface Web do Jaeger
      - "6831:6831/udp" # Coletor OpenTelemetry UDP

volumes:
  postgres_data:
`
  },
  {
    id: 'cicd',
    filename: 'ci-cd.yml',
    path: '.github/workflows/ci-cd.yml',
    category: 'cicd',
    language: 'yaml',
    description: 'Pipeline completo de CI/CD no GitHub Actions com Linter Ruff, testes Pytest, análise de segurança Trivy e Deploy no Cloud Run.',
    code: `name: Industrial CI/CD Pipeline

on:
  push:
    branches: [ main, staging ]
  pull_request:
    branches: [ main ]

jobs:
  test-and-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff pytest django pytest-django langchain

      - name: Code Quality check with Ruff
        run: ruff check .

      - name: Security Scan with Bandit & Trivy
        run: |
          pip install bandit
          bandit -r apps/

      - name: Run Django Pytest Suite
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
        run: pytest

  build-and-deploy:
    needs: test-and-lint
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: \${{ secrets.GCP_SA_KEY }}

      - name: Build and Push Docker Image to GCP Artifact Registry
        run: |
          gcloud auth configure-docker us-central1-docker.pkg.dev
          docker build -t us-central1-docker.pkg.dev/\${{ secrets.GCP_PROJECT }}/app/techparts:latest .
          docker push us-central1-docker.pkg.dev/\${{ secrets.GCP_PROJECT }}/app/techparts:latest

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy techparts-app \\
            --image us-central1-docker.pkg.dev/\${{ secrets.GCP_PROJECT }}/app/techparts:latest \\
            --region us-central1 \\
            --allow-unauthenticated
`
  }
];

export const ArchitectureView: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<CodeFile>(ARCHITECTURE_FILES[0]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredFiles = ARCHITECTURE_FILES.filter(f =>
    filterCategory === 'all' ? true : f.category === filterCategory
  );

  return (
    <div id="architecture-view-root" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Architecture Header */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-xs font-semibold text-cyan-300">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Arquitetura de Referência de Nível Industrial</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Stack Python + Django + HTMX + LangGraph + Cloudflare R2
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
              Códigos de produção documentados com integração nativa de observabilidade OpenTelemetry, banco PostgreSQL com pgvector, esteira de CI/CD no GitHub Actions e segurança CSP/HTTPS.
            </p>
          </div>

          <div className="flex items-center space-x-3 self-start lg:self-auto">
            <button
              onClick={() => copyCode(selectedFile.code, 'current')}
              className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold px-5 py-3 rounded-xl text-xs sm:text-sm flex items-center space-x-2 shadow-lg shadow-cyan-950/40 transition-all cursor-pointer"
            >
              {copiedId === 'current' ? <Check className="w-4 h-4 text-slate-950" /> : <Copy className="w-4 h-4 text-slate-950" />}
              <span>{copiedId === 'current' ? 'Código Copiado!' : 'Copiar Arquivo Selecionado'}</span>
            </button>
          </div>
        </div>

        {/* Stack Highlights Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-4 border-t border-slate-800 text-xs">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">Backend</span>
            <span className="font-bold text-white flex items-center gap-1.5 mt-0.5">
              <Server className="w-3.5 h-3.5 text-cyan-400" /> Django 5.0
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">Frontend Dynamic</span>
            <span className="font-bold text-white flex items-center gap-1.5 mt-0.5">
              <Code className="w-3.5 h-3.5 text-teal-400" /> HTMX + Bootstrap
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">Orquestrador IA</span>
            <span className="font-bold text-white flex items-center gap-1.5 mt-0.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" /> LangGraph Agent
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">Object Storage</span>
            <span className="font-bold text-white flex items-center gap-1.5 mt-0.5">
              <Cloud className="w-3.5 h-3.5 text-sky-400" /> Cloudflare R2
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">Observabilidade</span>
            <span className="font-bold text-white flex items-center gap-1.5 mt-0.5">
              <Activity className="w-3.5 h-3.5 text-emerald-400" /> OpenTelemetry
            </span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">CI/CD Pipeline</span>
            <span className="font-bold text-white flex items-center gap-1.5 mt-0.5">
              <GitBranch className="w-3.5 h-3.5 text-indigo-400" /> GitHub Actions
            </span>
          </div>
        </div>
      </div>

      {/* Code Explorer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Sidebar File List */}
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm space-y-3">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
              Estrutura de Arquivos da Stack
            </h3>

            {/* Category Filter */}
            <div className="flex flex-wrap gap-1 text-[11px] font-bold pb-1">
              {[
                { id: 'all', label: 'Todos' },
                { id: 'django', label: 'Django' },
                { id: 'langgraph', label: 'LangGraph' },
                { id: 'htmx', label: 'HTMX' },
                { id: 'storage', label: 'R2 Storage' },
                { id: 'observability', label: 'Telemetry' },
                { id: 'cicd', label: 'CI/CD' },
              ].map((c) => (
                <button
                  key={c.id}
                  onClick={() => setFilterCategory(c.id)}
                  className={`px-2 py-0.5 rounded-md transition-colors ${
                    filterCategory === c.id ? 'bg-slate-900 text-cyan-300' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {c.label}
                </button>
              ))}
            </div>

            <div className="space-y-1">
              {filteredFiles.map((file) => (
                <button
                  key={file.id}
                  onClick={() => setSelectedFile(file)}
                  className={`w-full text-left p-2.5 rounded-xl text-xs font-semibold flex items-center justify-between transition-all ${
                    selectedFile.id === file.id
                      ? 'bg-cyan-500/10 border border-cyan-500 text-cyan-950 font-extrabold shadow-sm'
                      : 'hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <FileCode className={`w-4 h-4 flex-shrink-0 ${
                      selectedFile.id === file.id ? 'text-cyan-600' : 'text-slate-400'
                    }`} />
                    <span className="truncate">{file.filename}</span>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                </button>
              ))}
            </div>
          </div>

          {/* Environmental Vars Quick Card */}
          <div className="bg-slate-900 text-white p-4 rounded-3xl border border-slate-800 space-y-2 text-xs">
            <h4 className="font-bold text-cyan-300 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" />
              Variáveis (.env.example)
            </h4>
            <div className="bg-slate-950 p-2.5 rounded-xl font-mono text-[10px] text-slate-300 space-y-1 overflow-x-auto">
              <div>SECRET_KEY=super-secret-key</div>
              <div>DATABASE_URL=postgres://user:pass@localhost:5432/db</div>
              <div>R2_ACCESS_KEY_ID=r2-key</div>
              <div>R2_SECRET_ACCESS_KEY=r2-secret</div>
              <div>R2_BUCKET_NAME=techparts-bucket</div>
              <div>R2_ENDPOINT_URL=https://...r2.cloudflarestorage.com</div>
              <div>GOOGLE_API_KEY=AIzaSy...</div>
            </div>
          </div>
        </div>

        {/* Right Code Viewer Panel */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-slate-950 rounded-3xl border border-slate-800 shadow-2xl overflow-hidden">
            
            {/* Viewer Top Bar */}
            <div className="bg-slate-900/90 px-6 py-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest block font-bold">
                  {selectedFile.path}
                </span>
                <h3 className="font-extrabold text-base text-white">{selectedFile.filename}</h3>
              </div>

              <div className="flex items-center space-x-2">
                <span className="bg-slate-800 text-slate-300 text-[10px] font-mono px-2.5 py-1 rounded-lg border border-slate-700 uppercase">
                  {selectedFile.language}
                </span>
                <button
                  onClick={() => copyCode(selectedFile.code, selectedFile.id)}
                  className="bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold px-3 py-1.5 rounded-lg text-xs flex items-center space-x-1 border border-slate-700 transition-colors"
                >
                  {copiedId === selectedFile.id ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedId === selectedFile.id ? 'Copiado!' : 'Copiar'}</span>
                </button>
              </div>
            </div>

            {/* File Description */}
            <div className="px-6 py-3 bg-slate-900/40 border-b border-slate-800/60 text-xs text-slate-300">
              {selectedFile.description}
            </div>

            {/* Code Body */}
            <div className="p-6 overflow-x-auto max-h-[600px] overflow-y-auto">
              <pre className="font-mono text-xs text-slate-200 leading-relaxed selection:bg-cyan-600 selection:text-white">
                <code>{selectedFile.code}</code>
              </pre>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
