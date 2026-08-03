import React, { useState } from 'react';
import { Ticket } from '../types';
import {
  Wrench,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  User,
  MessageSquare,
  Sparkles,
  X
} from 'lucide-react';

interface TicketsViewProps {
  tickets: Ticket[];
  onOpenNewTicket: (title: string, equipment: string, description: string) => void;
}

export const TicketsView: React.FC<TicketsViewProps> = ({ tickets, onOpenNewTicket }) => {
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New ticket state
  const [newTitle, setNewTitle] = useState('');
  const [newEquipment, setNewEquipment] = useState('');
  const [newDescription, setNewDescription] = useState('');

  const handleCreateTicket = (e: React.FormEvent) => {
    e.preventDefault();
    if (newTitle && newEquipment) {
      onOpenNewTicket(newTitle, newEquipment, newDescription);
      setNewTitle('');
      setNewEquipment('');
      setNewDescription('');
      setIsModalOpen(false);
      alert('Novo chamado técnico aberto com sucesso!');
    }
  };

  return (
    <div id="tickets-view-root" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Page Header */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 bg-slate-800 border border-slate-700 px-3 py-1 rounded-full text-xs font-semibold text-cyan-300 mb-2">
            <Wrench className="w-3.5 h-3.5 text-cyan-400" />
            <span>Área do Cliente & Manutenção</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white">Chamados Técnicos & Manutenção</h1>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Acompanhe o diagnóstico em tempo real, aprovação de peças e histórico de intervenções de campo.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold px-5 py-3 rounded-xl text-xs sm:text-sm flex items-center space-x-2 shadow-lg shadow-cyan-950/40 transition-all cursor-pointer whitespace-nowrap"
        >
          <Plus className="w-4 h-4 text-slate-950" />
          <span>Abrir Novo Chamado</span>
        </button>
      </div>

      {/* Tickets List */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-slate-900 text-sm">Histórico de Chamados Ativos ({tickets.length})</h3>
          <span className="text-xs text-slate-500 font-medium">Suporte 24/7 com Engenheiros IA</span>
        </div>

        <div className="divide-y divide-slate-100">
          {tickets.map((ticket) => (
            <div
              key={ticket.id}
              onClick={() => setSelectedTicket(ticket)}
              className="p-5 hover:bg-slate-50 transition-colors cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
            >
              <div className="space-y-1 max-w-2xl">
                <div className="flex items-center space-x-3">
                  <span className="font-mono text-xs font-bold text-cyan-700 bg-cyan-50 px-2.5 py-0.5 rounded border border-cyan-200">
                    {ticket.code}
                  </span>
                  <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                    ticket.status === 'Em Análise' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                    ticket.status === 'Aguardando Peça' ? 'bg-sky-50 text-sky-700 border-sky-200' :
                    'bg-teal-50 text-teal-700 border-teal-200'
                  }`}>
                    {ticket.status}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{ticket.date}</span>
                </div>

                <h4 className="font-bold text-sm text-slate-900 group-hover:text-cyan-700 transition-colors">
                  {ticket.title}
                </h4>

                <p className="text-xs text-slate-500 line-clamp-1">
                  Equipamento: <strong className="text-slate-700">{ticket.equipment}</strong> • {ticket.description}
                </p>
              </div>

              <div className="flex items-center space-x-4 flex-shrink-0">
                <div className="text-right hidden sm:block text-xs">
                  <span className="text-slate-400 block text-[10px]">Técnico Responsável</span>
                  <span className="font-bold text-slate-800">{ticket.technician}</span>
                </div>
                <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-cyan-600 transition-colors" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Ticket Details Drawer Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 text-white max-w-2xl w-full rounded-3xl border border-slate-800 shadow-2xl p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950 px-2.5 py-1 rounded border border-cyan-800">
                  {selectedTicket.code}
                </span>
                <h3 className="font-bold text-base text-slate-100">{selectedTicket.title}</h3>
              </div>
              <button
                onClick={() => setSelectedTicket(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4 bg-slate-950 p-4 rounded-2xl border border-slate-800">
                <div>
                  <span className="text-slate-400 block">Equipamento:</span>
                  <span className="font-bold text-slate-200">{selectedTicket.equipment}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Status Atual:</span>
                  <span className="font-bold text-cyan-400">{selectedTicket.status}</span>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[11px]">Linha do Tempo de Resolução</h4>
                <div className="space-y-2">
                  {selectedTicket.history.map((h, i) => (
                    <div key={i} className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span>{h.author}</span>
                        <span className="font-mono">{h.date}</span>
                      </div>
                      <p className="text-slate-200">{h.note}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => setSelectedTicket(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold px-4 py-2 rounded-xl text-xs"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Ticket Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleCreateTicket} className="bg-white text-slate-900 max-w-lg w-full rounded-3xl border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-base text-slate-900">Abrir Novo Chamado Técnico</h3>
              <button type="button" onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Título do Sintoma / Problema</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Ex: Vibração atípica no exaustor industrial"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Modelo / Identificação do Equipamento</label>
                <input
                  type="text"
                  required
                  value={newEquipment}
                  onChange={(e) => setNewEquipment(e.target.value)}
                  placeholder="Ex: Exaustor Linha V-400"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Descrição Detalhada do Ocorrido</label>
                <textarea
                  rows={3}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Relate aquecimento, ruidos ou paradas abruptas..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-4 py-2 rounded-xl text-xs"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-5 py-2 rounded-xl text-xs shadow-sm"
              >
                Gerar Chamado
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
