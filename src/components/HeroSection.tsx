import React, { useState } from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Zap, Cpu } from 'lucide-react';

interface HeroSectionProps {
  onStartDiagnostic: (initialQuery: string) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onStartDiagnostic }) => {
  const [heroPrompt, setHeroPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (heroPrompt.trim()) {
      onStartDiagnostic(heroPrompt);
    }
  };

  return (
    <div id="hero-banner-container" className="relative bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 text-white border-b border-slate-800 overflow-hidden">
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b15_1px,transparent_1px),linear-gradient(to_bottom,#1e293b15_1px,transparent_1px)] bg-[size:32px_32px] opacity-60" />
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-14">
        <div className="max-w-3xl">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 bg-slate-800/90 border border-slate-700/80 px-3 py-1 rounded-full text-xs font-semibold text-cyan-300 mb-4 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Motor Neural de Compatibilidade Industrial</span>
          </div>

          {/* Heading */}
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">
            Precisão em <span className="bg-clip-text text-transparent bg-gradient-to-r from-teal-300 via-cyan-400 to-sky-400">Diagnóstico Técnico</span>
          </h1>

          {/* Subtitle */}
          <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed font-normal max-w-2xl">
            Nossa IA analisa sintomas, identifica a causa raiz e recomenda a peça de substituição exata para seu maquinário sem margem de erro.
          </p>

          {/* AI Quick Diagnostic Bar */}
          <form id="hero-diagnostic-form" onSubmit={handleSubmit} className="mt-6 bg-slate-950/90 p-2 rounded-2xl border border-slate-700/80 shadow-2xl flex flex-col sm:flex-row items-stretch gap-2">
            <div className="flex-1 flex items-center px-3 py-1 space-x-2">
              <Cpu className="w-5 h-5 text-cyan-400 flex-shrink-0" />
              <input
                id="hero-diagnostic-input"
                type="text"
                value={heroPrompt}
                onChange={(e) => setHeroPrompt(e.target.value)}
                placeholder="Descreva o sintoma (Ex: Ventilador Mondial parou com cheiro de queimado...)"
                className="w-full bg-transparent text-slate-100 placeholder-slate-400 text-xs sm:text-sm focus:outline-none"
              />
            </div>
            <button
              id="hero-analyze-btn"
              type="submit"
              className="bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold px-5 py-3 rounded-xl text-xs sm:text-sm flex items-center justify-center space-x-2 shadow-lg shadow-cyan-950/50 transition-all cursor-pointer"
            >
              <span>Analisar com IA</span>
              <ArrowRight className="w-4 h-4 text-slate-950" />
            </button>
          </form>

          {/* Quick Stats / Trust Badges */}
          <div id="hero-trust-badges" className="mt-6 grid grid-cols-3 gap-4 pt-4 border-t border-slate-800/80">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-teal-400 flex-shrink-0" />
              <span className="text-xs text-slate-300 font-medium">99.4% Compatibilidade</span>
            </div>
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span className="text-xs text-slate-300 font-medium">Resposta em &lt;1 Seg.</span>
            </div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span className="text-xs text-slate-300 font-medium">Garantia Fabril 100%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
