import React, { useState, useRef } from 'react';
import { Product, ChatMessage } from '../types';
import {
  Sparkles,
  Printer,
  Share2,
  Search,
  FileText,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  Camera,
  Volume2,
  History,
  Paperclip,
  Send,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShoppingCart,
  Loader2,
  User,
  ShieldAlert
} from 'lucide-react';

interface DiagnosticChatViewProps {
  messages: ChatMessage[];
  onSendMessage: (text: string, imageBase64?: string) => void;
  products: Product[];
  onAddToCart: (product: Product) => void;
  onSelectProduct: (product: Product) => void;
  isLoading: boolean;
  initialQuery?: string;
}

export const DiagnosticChatView: React.FC<DiagnosticChatViewProps> = ({
  messages,
  onSendMessage,
  products,
  onAddToCart,
  onSelectProduct,
  isLoading,
  initialQuery
}) => {
  const [inputText, setInputText] = useState(initialQuery || '');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if ((inputText.trim() || selectedImage) && !isLoading) {
      onSendMessage(inputText, selectedImage || undefined);
      setInputText('');
      setSelectedImage(null);
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerQuickPrompt = (prompt: string) => {
    setInputText(prompt);
  };

  return (
    <div id="diagnostic-chat-root" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      
      {/* Top Header Bar */}
      <div id="chat-header-bar" className="bg-slate-900 text-white p-4 rounded-t-2xl border border-slate-800 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-500 text-slate-950 flex items-center justify-center font-bold">
            <Sparkles className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              Assistente de Diagnóstico AI
              <span className="bg-teal-950 text-teal-300 text-[10px] font-mono px-2 py-0.5 rounded border border-teal-800">
                MOTOR DE DIAGNÓSTICO V4.2 ATIVO
              </span>
            </h2>
            <p className="text-xs text-slate-400">Análise técnica em tempo real com base em esquemas fabris e telemetria</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => window.print()}
            className="p-2 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            title="Imprimir relatório técnico"
          >
            <Printer className="w-4 h-4" />
          </button>
          <button
            onClick={() => alert('Link do diagnóstico copiado para a área de transferência!')}
            className="p-2 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            title="Compartilhar com a equipe"
          >
            <Share2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Container Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 bg-slate-950 rounded-b-2xl border-x border-b border-slate-800 shadow-2xl min-h-[620px]">
        
        {/* Left Sidebar: Conversations & Docs */}
        <aside id="chat-sidebar-left" className="lg:col-span-1 border-r border-slate-800 p-4 space-y-5 bg-slate-900/60 rounded-bl-2xl">
          {/* Conversation Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Buscar conversas..."
              className="w-full bg-slate-950 text-slate-200 placeholder-slate-500 text-xs rounded-xl pl-8 pr-3 py-2 border border-slate-800 focus:outline-none focus:border-cyan-500"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
          </div>

          {/* Recent Conversations */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block px-1">
              Histórico Recente
            </span>
            <div className="space-y-1">
              {[
                { title: 'Ventilador V-400 - Parou', date: 'Hoje, 14:22', active: true },
                { title: 'Motor Trifásico - Superaquecimento', date: 'Ontem', active: false },
                { title: 'Substituição de Rolamentos', date: '30 Jul', active: false }
              ].map((item, idx) => (
                <button
                  key={idx}
                  className={`w-full text-left p-2.5 rounded-xl text-xs transition-all ${
                    item.active
                      ? 'bg-slate-800 text-cyan-300 border border-slate-700 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <div className="truncate">{item.title}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{item.date}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Related PDFs */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block px-1">
              Documentação Relacionada
            </span>
            <div className="space-y-1.5">
              <a
                href="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-2 text-xs text-slate-300 hover:text-cyan-400 p-2 rounded-lg hover:bg-slate-900 transition-colors"
              >
                <FileText className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <span className="truncate">Manual V-Series 2024 (PDF)</span>
              </a>
              <a
                href="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-2 text-xs text-slate-300 hover:text-cyan-400 p-2 rounded-lg hover:bg-slate-900 transition-colors"
              >
                <FileText className="w-4 h-4 text-cyan-500 flex-shrink-0" />
                <span className="truncate">Guia de Solução de Falhas</span>
              </a>
            </div>
          </div>

          {/* Low Confidence / Specialist Support Box */}
          <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800 space-y-2 mt-auto">
            <div className="flex items-center space-x-1.5 text-amber-400 text-xs font-bold">
              <HelpCircle className="w-4 h-4" />
              <span>Precisa de validação humana?</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-tight">
              Se a divergência elétrica for superior a 15%, transfira para um engenheiro de campo.
            </p>
            <button
              onClick={() => alert('Chamado urgente gerado para o Engenheiro de Campo Plantonista.')}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold py-1.5 rounded-lg border border-slate-700 transition-colors"
            >
              Falar com Especialista
            </button>
          </div>
        </aside>

        {/* Main Diagnostic Chat Thread Area */}
        <main id="chat-main-thread" className="lg:col-span-3 flex flex-col justify-between p-4 sm:p-6 space-y-6">
          
          {/* Messages Container */}
          <div className="space-y-6 overflow-y-auto max-h-[500px] pr-2">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'ai' && (
                  <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 flex items-center justify-center flex-shrink-0 font-bold">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-2xl space-y-3 ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Text Bubble */}
                  <div
                    className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                      msg.sender === 'user'
                        ? 'bg-cyan-600 text-white rounded-tr-none'
                        : 'bg-slate-900 text-slate-200 border border-slate-800 rounded-tl-none shadow-md'
                    }`}
                  >
                    {msg.image && (
                      <div className="mb-3 rounded-lg overflow-hidden border border-slate-700">
                        <img src={msg.image} alt="Anexo de diagnóstico" referrerPolicy="no-referrer" className="max-h-48 object-cover w-full" />
                      </div>
                    )}
                    <p>{msg.text}</p>
                  </div>

                  {/* Diagnostic Summary Card (If AI responded) */}
                  {msg.diagnosisCard && (
                    <div id="ai-diagnosis-card" className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <span className="text-xs font-extrabold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-teal-400" />
                          {msg.diagnosisCard.title}
                        </span>
                        <span className="bg-teal-950 text-teal-300 text-xs font-bold px-2.5 py-1 rounded-full border border-teal-800">
                          {msg.diagnosisCard.confidence}% CONFIANÇA
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed">
                        {msg.diagnosisCard.description}
                      </p>

                      {/* REF Citation Box */}
                      <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-[11px] font-mono text-cyan-300/90 flex items-start space-x-2">
                        <FileText className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                        <span>{msg.diagnosisCard.refManual}</span>
                      </div>

                      {/* Recommended Parts list */}
                      <div className="space-y-2 pt-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                          Componentes de Substituição Recomendados:
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {products
                            .filter(p => msg.diagnosisCard?.recommendedSkus.includes(p.sku) || p.sku === 'SKU-CAP-45UF' || p.sku === 'SKU-FUS-135C')
                            .slice(0, 2)
                            .map((part) => (
                              <div
                                key={part.id}
                                className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center justify-between gap-2 hover:border-slate-700 transition-colors"
                              >
                                <div className="space-y-0.5 min-w-0">
                                  <span className="text-[10px] font-mono text-slate-400 block truncate">{part.sku}</span>
                                  <h5 className="font-bold text-xs text-slate-100 truncate">{part.name}</h5>
                                  <span className="text-xs font-black text-cyan-400">
                                    R$ {part.price.toFixed(2).replace('.', ',')}
                                  </span>
                                </div>
                                <button
                                  onClick={() => onAddToCart(part)}
                                  className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs flex items-center space-x-1 flex-shrink-0 cursor-pointer shadow-sm"
                                >
                                  <ShoppingCart className="w-3.5 h-3.5" />
                                  <span>Comprar</span>
                                </button>
                              </div>
                            ))}
                        </div>
                      </div>

                      {/* Footer feedback row */}
                      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/60">
                        <span>Tempo de análise: {msg.responseTime || '0.8s'}</span>
                        <div className="flex items-center space-x-2">
                          <span>Diagnóstico útil?</span>
                          <button className="p-1 hover:text-teal-400 transition-colors">
                            <ThumbsUp className="w-3.5 h-3.5" />
                          </button>
                          <button className="p-1 hover:text-red-400 transition-colors">
                            <ThumbsDown className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {msg.sender === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 text-slate-300 flex items-center justify-center flex-shrink-0 font-bold">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center space-x-3 text-cyan-400 text-xs bg-slate-900 p-4 rounded-2xl border border-slate-800 w-fit">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processando esquemas técnicos e gerando diagnóstico neural...</span>
              </div>
            )}
          </div>

          {/* Complex Diagnostic Alert Banner */}
          <div className="bg-amber-950/40 border border-amber-800/60 p-3 rounded-xl flex items-center justify-between text-xs text-amber-200">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>Diagnóstico Complexo Detectado: Se houver vibração mecânica atípica, realize inspeção de alinhamento com estroboscópio.</span>
            </div>
            <button
              onClick={() => alert('Solicitação enviada ao supervisor do turno!')}
              className="text-amber-300 underline font-bold whitespace-nowrap ml-2 hover:text-white"
            >
              Solicitar Técnico
            </button>
          </div>

          {/* Quick Action Pills & Input Bar */}
          <div className="space-y-3">
            {/* Quick Action Pills */}
            <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium px-3 py-1.5 rounded-lg border border-slate-800 flex items-center space-x-1.5 whitespace-nowrap transition-colors"
              >
                <Camera className="w-3.5 h-3.5 text-cyan-400" />
                <span>ANALISAR FOTO</span>
              </button>

              <button
                onClick={() => triggerQuickPrompt('Executar análise espectral do ruído de vibração do motor')}
                className="bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium px-3 py-1.5 rounded-lg border border-slate-800 flex items-center space-x-1.5 whitespace-nowrap transition-colors"
              >
                <Volume2 className="w-3.5 h-3.5 text-amber-400" />
                <span>ANÁLISE DE RUÍDO</span>
              </button>

              <button
                onClick={() => triggerQuickPrompt('Consultar histórico de substituições deste SKU no último ano')}
                className="bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium px-3 py-1.5 rounded-lg border border-slate-800 flex items-center space-x-1.5 whitespace-nowrap transition-colors"
              >
                <History className="w-3.5 h-3.5 text-teal-400" />
                <span>HISTÓRICO DE MANUTENÇÃO</span>
              </button>
            </div>

            {/* Hidden file input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageUpload}
              accept="image/*"
              className="hidden"
            />

            {/* Input Box */}
            <form onSubmit={handleSend} className="relative flex items-center">
              {selectedImage && (
                <div className="absolute left-3 top-[-36px] bg-slate-900 px-2 py-1 rounded border border-slate-700 text-[10px] text-cyan-300 flex items-center gap-1">
                  <span>Foto Anexada</span>
                  <button type="button" onClick={() => setSelectedImage(null)} className="text-red-400 font-bold ml-1">×</button>
                </div>
              )}

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="absolute left-3 text-slate-400 hover:text-cyan-400 transition-colors"
                title="Anexar imagem do componente ou placa"
              >
                <Paperclip className="w-4 h-4" />
              </button>

              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Descreva o problema técnico aqui (Ex: Motor aquece em 10 min e disjuntor desarma...)"
                className="w-full bg-slate-900 text-slate-100 placeholder-slate-500 text-xs sm:text-sm rounded-2xl pl-10 pr-12 py-3.5 border border-slate-800 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 shadow-inner"
              />

              <button
                type="submit"
                disabled={isLoading || (!inputText.trim() && !selectedImage)}
                className="absolute right-2 bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 disabled:opacity-40 text-slate-950 p-2 rounded-xl transition-all shadow-md cursor-pointer"
              >
                <Send className="w-4 h-4 text-slate-950" />
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
};
