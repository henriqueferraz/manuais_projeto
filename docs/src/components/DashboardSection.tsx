import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  CartesianGrid
} from 'recharts';
import {
  TrendingUp,
  PackageCheck,
  Search,
  Sparkles,
  BarChart3,
  PieChart as PieIcon,
  Activity,
  Layers,
  ArrowUpRight,
  ShieldCheck,
  Zap,
  Info
} from 'lucide-react';

// Data for Chart 1: Volume de peças em estoque
const STOCK_VOLUME_DATA = [
  { category: 'Linha HVAC', estoque: 420, minimo: 150, reservado: 60 },
  { category: 'Sensores', estoque: 310, minimo: 100, reservado: 45 },
  { category: 'Motores', estoque: 280, minimo: 120, reservado: 30 },
  { category: 'Componentes', estoque: 250, minimo: 80, reservado: 20 },
  { category: 'Partes & Hélices', estoque: 220, minimo: 90, reservado: 15 },
];

// Data for Chart 2: Categorias mais buscadas
const SEARCHED_CATEGORIES_DATA = [
  { name: 'Linha HVAC & Exaustores', value: 38, count: '4.730 buscas', color: '#06b6d4' },
  { name: 'Sensores de Precisão', value: 24, count: '2.980 buscas', color: '#14b8a6' },
  { name: 'Motores & Compressores', value: 20, count: '2.490 buscas', color: '#0284c7' },
  { name: 'Componentes Eletrônicos', value: 12, count: '1.490 buscas', color: '#6366f1' },
  { name: 'Partes Estruturais', value: 6, count: '760 buscas', color: '#a855f7' },
];

// Data for Chart 3: Eficiência dos diagnósticos realizados pela IA
const AI_EFFICIENCY_DATA = [
  { period: 'Sem 1', precisao: 92.4, resolucaoDirecta: 88.0, tempoSeg: 1.4 },
  { period: 'Sem 2', precisao: 94.1, resolucaoDirecta: 90.2, tempoSeg: 1.2 },
  { period: 'Sem 3', precisao: 95.8, resolucaoDirecta: 92.5, tempoSeg: 1.0 },
  { period: 'Sem 4', precisao: 97.2, resolucaoDirecta: 94.8, tempoSeg: 0.9 },
  { period: 'Sem 5', precisao: 98.0, resolucaoDirecta: 96.1, tempoSeg: 0.8 },
  { period: 'Sem 6', precisao: 98.8, resolucaoDirecta: 97.4, tempoSeg: 0.7 },
];

interface DashboardSectionProps {
  onOpenConsultant?: () => void;
}

export const DashboardSection: React.FC<DashboardSectionProps> = ({ onOpenConsultant }) => {
  const [timeframe, setTimeframe] = useState<'7d' | '30d' | '90d'>('30d');
  const [activeTab, setActiveTab] = useState<'all' | 'stock' | 'searches' | 'ai'>('all');

  const totalStock = STOCK_VOLUME_DATA.reduce((acc, curr) => acc + curr.estoque, 0);
  const totalSearches = '12.450';
  const aiAccuracy = '98.8%';
  const avgResponseTime = '0.7s';

  return (
    <section id="initial-dashboard-root" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header Bar of Dashboard */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center space-x-2 bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-xs font-semibold text-cyan-300">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span>Painel de Telemetria & Operações</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Dashboard de Estoque & Inteligência Artificial
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl">
              Monitoramento em tempo real do inventário industrial, volume de buscas por categoria e indicadores de precisão do assistente preditivo.
            </p>
          </div>

          {/* Timeframe & Controls */}
          <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
            <div className="bg-slate-950 p-1 rounded-xl border border-slate-800 flex items-center text-xs font-bold">
              {(['7d', '30d', '90d'] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={`px-3 py-1.5 rounded-lg transition-all ${
                    timeframe === tf
                      ? 'bg-cyan-500 text-slate-950 shadow-sm font-extrabold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {tf === '7d' ? '7 Dias' : tf === '30d' ? '30 Dias' : '90 Dias'}
                </button>
              ))}
            </div>

            {onOpenConsultant && (
              <button
                onClick={onOpenConsultant}
                className="bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold px-4 py-2 rounded-xl text-xs flex items-center space-x-2 border border-slate-700 transition-colors cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>Iniciar Diagnóstico</span>
              </button>
            )}
          </div>
        </div>

        {/* KPI Cards Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-slate-800">
          
          <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[10px] font-bold uppercase tracking-wider">Total em Estoque</span>
              <PackageCheck className="w-4 h-4 text-teal-400" />
            </div>
            <div className="text-2xl font-black text-white">{totalStock.toLocaleString('pt-BR')} <span className="text-xs font-normal text-slate-400">unid</span></div>
            <div className="text-[10px] font-semibold text-teal-400 flex items-center gap-1">
              <ArrowUpRight className="w-3 h-3" />
              <span>+8.4% este mês</span>
            </div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[10px] font-bold uppercase tracking-wider">Buscas por Peças</span>
              <Search className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-black text-white">{totalSearches}</div>
            <div className="text-[10px] font-semibold text-cyan-400 flex items-center gap-1">
              <ArrowUpRight className="w-3 h-3" />
              <span>+14.2% consultas</span>
            </div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[10px] font-bold uppercase tracking-wider">Assertividade IA</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400">{aiAccuracy}</div>
            <div className="text-[10px] font-semibold text-emerald-300 flex items-center gap-1">
              <span>99.1% compatibilidade</span>
            </div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[10px] font-bold uppercase tracking-wider">Tempo Diagnóstico</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-black text-amber-300">{avgResponseTime}</div>
            <div className="text-[10px] font-semibold text-amber-400 flex items-center gap-1">
              <span>Sub-segundo preditivo</span>
            </div>
          </div>

        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CHART 1: Volume de Peças em Estoque (BarChart) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-cyan-600" />
                <h3 className="font-bold text-slate-900 text-sm">1. Volume de Peças em Estoque por Categoria</h3>
              </div>
              <p className="text-xs text-slate-500">
                Quantidade atual de itens disponíveis vs. margem de segurança buffer
              </p>
            </div>
            <span className="text-[11px] font-bold bg-cyan-50 text-cyan-700 px-2.5 py-1 rounded-lg border border-cyan-200 self-start sm:self-auto">
              Total: 1.480 Unidades
            </span>
          </div>

          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={STOCK_VOLUME_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '12px',
                    color: '#f8fafc',
                    fontSize: '12px'
                  }}
                  cursor={{ fill: 'rgba(226, 232, 240, 0.4)' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="estoque" name="Estoque Atual" fill="#06b6d4" radius={[6, 6, 0, 0]} barSize={28} />
                <Bar dataKey="minimo" name="Estoque Mínimo (Buffer)" fill="#94a3b8" radius={[6, 6, 0, 0]} barSize={28} />
                <Bar dataKey="reservado" name="Reservado em Pedidos" fill="#0d9488" radius={[6, 6, 0, 0]} barSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* CHART 2: Categorias Mais Buscadas (PieChart / Donut) */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
              <PieIcon className="w-4 h-4 text-teal-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">2. Categorias Mais Buscadas</h3>
                <p className="text-xs text-slate-500">Distribuição percentual da demanda técnica</p>
              </div>
            </div>

            <div className="h-56 w-full my-2">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={SEARCHED_CATEGORIES_DATA}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {SEARCHED_CATEGORIES_DATA.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#1e293b',
                      borderRadius: '12px',
                      color: '#f8fafc',
                      fontSize: '12px'
                    }}
                    formatter={(val: any) => [`${val}% das buscas`, 'Participação']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category List Details */}
          <div className="space-y-2 pt-2 border-t border-slate-100 text-xs">
            {SEARCHED_CATEGORIES_DATA.map((cat) => (
              <div key={cat.name} className="flex items-center justify-between">
                <div className="flex items-center space-x-2 truncate">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color }} />
                  <span className="font-medium text-slate-700 truncate">{cat.name}</span>
                </div>
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <span className="font-extrabold text-slate-900">{cat.value}%</span>
                  <span className="text-[10px] text-slate-400 font-mono">({cat.count})</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* CHART 3: Eficiência dos Diagnósticos Realizados pela IA (AreaChart) */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-cyan-600" />
              <h3 className="font-bold text-slate-900 text-sm">
                3. Evolução da Eficiência dos Diagnósticos Realizados pela IA
              </h3>
            </div>
            <p className="text-xs text-slate-500">
              Taxa de precisão diagnóstica (%) e taxa de solução na primeira resposta nas últimas 6 semanas
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <span className="flex items-center text-teal-700 font-bold bg-teal-50 px-2.5 py-1 rounded-lg border border-teal-200">
              <span className="w-2 h-2 rounded-full bg-teal-500 mr-1.5" />
              Precisão: 98.8%
            </span>
            <span className="flex items-center text-cyan-700 font-bold bg-cyan-50 px-2.5 py-1 rounded-lg border border-cyan-200">
              <span className="w-2 h-2 rounded-full bg-cyan-500 mr-1.5" />
              Tempo Médio: 0.7s
            </span>
          </div>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={AI_EFFICIENCY_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
              <defs>
                <linearGradient id="colorPrecisao" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorResolucao" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis domain={[80, 100]} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#1e293b',
                  borderRadius: '12px',
                  color: '#f8fafc',
                  fontSize: '12px'
                }}
                formatter={(val: any, name: string) => [
                  name === 'tempoSeg' ? `${val}s` : `${val}%`,
                  name === 'precisao'
                    ? 'Precisão Diagnóstica (%)'
                    : name === 'resolucaoDirecta'
                    ? 'Resolução em 1º Chamado (%)'
                    : 'Tempo de Resposta (s)'
                ]}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Area
                type="monotone"
                dataKey="precisao"
                name="Precisão Diagnóstica IA (%)"
                stroke="#14b8a6"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorPrecisao)"
              />
              <Area
                type="monotone"
                dataKey="resolucaoDirecta"
                name="Resolução Direta de Problemas (%)"
                stroke="#06b6d4"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorResolucao)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* AI Insight Footer Note */}
        <div className="bg-slate-900 text-slate-200 p-4 rounded-2xl border border-slate-800 flex items-start space-x-3 text-xs">
          <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-white">Insight da Rede Neural:</strong> O aumento na precisão para 98.8% correlaciona-se com a ingestão contínua de manuais em PDF. A taxa de falso diagnóstico para motores e exaustores reduziu-se a praticamente zero no último ciclo.
          </p>
        </div>
      </div>

    </section>
  );
};
