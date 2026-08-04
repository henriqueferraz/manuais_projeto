import React, { useState } from 'react';
import { ManualReview } from '../types';
import {
  FileText,
  Upload,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Eye,
  SlidersHorizontal,
  Sparkles,
  Check,
  X,
  FileCheck,
  Cpu
} from 'lucide-react';

interface AdminManualsViewProps {
  manuals: ManualReview[];
  onApproveManual: (id: string) => void;
  onUploadManual: (file: File) => void;
}

export const AdminManualsView: React.FC<AdminManualsViewProps> = ({
  manuals,
  onApproveManual,
  onUploadManual
}) => {
  const [selectedManual, setSelectedManual] = useState<ManualReview | null>(null);
  const [searchFilter, setSearchFilter] = useState('');

  const filteredManuals = manuals.filter(m =>
    m.filename.toLowerCase().includes(searchFilter.toLowerCase()) ||
    m.manufacturer.toLowerCase().includes(searchFilter.toLowerCase()) ||
    m.skuCode.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div id="admin-manuals-root" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Admin Header */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-xs font-semibold text-cyan-300 mb-2">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>Painel de Ingestão de Manuais por IA</span>
            </div>
            <h1 className="text-2xl font-black text-white">Fila de Revisão de Manuais Técnicos</h1>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl">
              Gerencie e valide as extrações automatizadas de arquivos PDF para garantir 100% de precisão nos atributos do catálogo.
            </p>
          </div>

          <label className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold px-5 py-3 rounded-xl text-xs sm:text-sm flex items-center space-x-2 shadow-lg shadow-cyan-950/40 transition-all cursor-pointer whitespace-nowrap self-start md:self-auto">
            <Upload className="w-4 h-4 text-slate-950" />
            <span>+ Upload de Manual PDF</span>
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onUploadManual(file);
              }}
            />
          </label>
        </div>

        {/* KPI Metric Cards matching screenshot */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800/80">
          <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">Aguardando Revisão</span>
            <div className="text-2xl font-black text-amber-400 mt-1">12 <span className="text-xs font-normal text-slate-400">PDFs</span></div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">Processados Hoje</span>
            <div className="text-2xl font-black text-teal-400 mt-1">45 <span className="text-xs font-semibold text-teal-300/80 text-[11px]">(+12% em relação a ontem)</span></div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-2xl border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">Erros de Extração</span>
            <div className="text-2xl font-black text-red-400 mt-1">03 <span className="text-xs font-normal text-slate-400">(Requer atenção)</span></div>
          </div>
        </div>
      </div>

      {/* Manuals Table Container */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        
        {/* Table Filter Bar */}
        <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Buscar por fabricante, PDF ou SKU..."
              className="w-full bg-slate-50 text-slate-800 placeholder-slate-400 text-xs rounded-xl pl-8 pr-3 py-2 border border-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </div>

          <span className="text-xs text-slate-500 font-medium">
            Capacidade IA: <strong className="text-teal-600">98.2% Processamento Otimizado</strong>
          </span>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Arquivo PDF</th>
                <th className="py-3 px-4">Fabricante</th>
                <th className="py-3 px-4">SKU Associado</th>
                <th className="py-3 px-4">Data do Upload</th>
                <th className="py-3 px-4">Confiança IA</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredManuals.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-900 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-cyan-600 flex-shrink-0" />
                    <span className="truncate max-w-[200px]">{m.filename}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-700 font-semibold">{m.manufacturer}</td>
                  <td className="py-3.5 px-4 font-mono text-slate-500">{m.skuCode}</td>
                  <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px]">{m.uploadDate}</td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            m.confidence >= 85 ? 'bg-teal-500' : m.confidence >= 70 ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${m.confidence}%` }}
                        />
                      </div>
                      <span className="font-extrabold text-[11px] text-slate-800">{m.confidence}%</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                      m.status === 'Aprovado' ? 'bg-teal-50 text-teal-700 border-teal-200' :
                      m.status === 'Aguardando Revisão' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                      'bg-red-50 text-red-700 border-red-200'
                    }`}>
                      {m.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => setSelectedManual(m)}
                      className="bg-slate-900 hover:bg-slate-800 text-cyan-300 font-bold px-3 py-1.5 rounded-lg text-xs transition-colors"
                    >
                      Revisar Dados
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Review Drawer Modal */}
      {selectedManual && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 text-white max-w-2xl w-full rounded-3xl border border-slate-800 shadow-2xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <FileCheck className="w-5 h-5 text-cyan-400" />
                <h3 className="font-bold text-base text-slate-100">{selectedManual.filename}</h3>
              </div>
              <button onClick={() => setSelectedManual(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <span className="text-slate-400 block font-semibold">Atributos Extraídos pelo Modelo de Leitura de PDFs:</span>
              <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2 font-mono">
                {Object.entries(selectedManual.extractedData).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-slate-900 pb-1.5">
                    <span className="text-slate-400 uppercase">{k}:</span>
                    <span className="text-cyan-300 font-bold">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setSelectedManual(null)}
                className="bg-slate-800 text-slate-300 font-bold px-4 py-2 rounded-xl text-xs"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  onApproveManual(selectedManual.id);
                  setSelectedManual(null);
                  alert('Extração do manual aprovada e sincronizada ao catálogo com sucesso!');
                }}
                className="bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold px-5 py-2 rounded-xl text-xs flex items-center space-x-1"
              >
                <Check className="w-4 h-4 text-slate-950" />
                <span>Aprovar & Ingerir ao Catálogo</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
