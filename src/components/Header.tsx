import React from 'react';
import { ViewMode } from '../types';
import {
  Cpu,
  Search,
  ShoppingCart,
  Wrench,
  FileText,
  Sparkles,
  Image as ImageIcon,
  User,
  CheckCircle2,
  SlidersHorizontal,
  BarChart3
} from 'lucide-react';

interface HeaderProps {
  currentView: ViewMode;
  setCurrentView: (view: ViewMode) => void;
  cartCount: number;
  openCart: () => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  openImageLinksModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  setCurrentView,
  cartCount,
  openCart,
  searchQuery,
  setSearchQuery,
  openImageLinksModal
}) => {
  return (
    <header id="main-header" className="bg-slate-900 text-slate-100 border-b border-slate-800 sticky top-0 z-40 shadow-lg">
      {/* Top Banner / Utility Bar */}
      <div id="top-utility-bar" className="bg-slate-950 text-slate-400 text-xs py-1.5 px-4 flex items-center justify-between border-b border-slate-800/60">
        <div className="flex items-center space-x-3">
          <span className="flex items-center text-teal-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse mr-1.5" />
            MOTOR DE DIAGNÓSTICO V4.2 ATIVO
          </span>
          <span className="hidden md:inline text-slate-500">•</span>
          <span className="hidden md:inline">Garantia Técnica Fabril & Frete Expresso Industrial</span>
        </div>
        <div className="flex items-center space-x-4">
          <button
            id="open-image-links-btn"
            onClick={openImageLinksModal}
            className="flex items-center space-x-1 hover:text-teal-300 text-slate-300 transition-colors"
            title="Acessar links diretos das imagens HTML"
          >
            <ImageIcon className="w-3.5 h-3.5 text-teal-400" />
            <span className="font-medium">Links Diretos Imagens</span>
          </button>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">Suporte Técnico: 0800-770-TECH</span>
        </div>
      </div>

      {/* Primary Navigation Bar */}
      <div id="primary-nav-bar" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div id="brand-logo-container" className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentView('catalog')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-600 flex items-center justify-center text-slate-950 font-black shadow-md shadow-cyan-950/50">
            <Cpu className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="text-xl font-black tracking-tight text-white font-sans">
                TechParts<span className="text-cyan-400">.AI</span>
              </span>
              <span className="bg-cyan-950 text-cyan-300 text-[10px] font-bold px-1.5 py-0.5 rounded border border-cyan-800/60">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-wide font-medium">Automação & Diagnóstico Técnico</p>
          </div>
        </div>

        {/* Global Search Input */}
        <div id="global-search-container" className="hidden lg:flex flex-1 max-w-md relative">
          <input
            id="global-search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por SKU, modelo do equipamento (Ex: VTE-02, 1LE1) ou sintoma..."
            className="w-full bg-slate-950/80 text-slate-100 placeholder-slate-400 text-xs rounded-lg pl-9 pr-4 py-2.5 border border-slate-700/80 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
        </div>

        {/* Navigation Mode Tabs */}
        <nav id="header-nav-tabs" className="hidden md:flex items-center space-x-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
          <button
            id="nav-tab-catalog"
            onClick={() => setCurrentView('catalog')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              currentView === 'catalog' || currentView === 'product_detail'
                ? 'bg-slate-800 text-cyan-300 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <span>Catálogo</span>
          </button>

          <button
            id="nav-tab-dashboard"
            onClick={() => setCurrentView('dashboard')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              currentView === 'dashboard'
                ? 'bg-slate-800 text-cyan-300 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Dashboard</span>
          </button>

          <button
            id="nav-tab-diagnostic"
            onClick={() => setCurrentView('diagnostic')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              currentView === 'diagnostic'
                ? 'bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-md shadow-cyan-900/40'
                : 'text-slate-300 hover:text-white hover:bg-slate-900/50'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
            <span>Assistente IA</span>
          </button>

          <button
            id="nav-tab-tickets"
            onClick={() => setCurrentView('tickets')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              currentView === 'tickets'
                ? 'bg-slate-800 text-cyan-300 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <Wrench className="w-3.5 h-3.5" />
            <span>Chamados</span>
          </button>

          <button
            id="nav-tab-admin"
            onClick={() => setCurrentView('admin_manuals')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              currentView === 'admin_manuals'
                ? 'bg-slate-800 text-cyan-300 shadow-sm border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Fila Manuais</span>
          </button>
        </nav>

        {/* Right Controls (Cart, User Avatar, Mobile Menu) */}
        <div id="header-right-actions" className="flex items-center space-x-3">
          <button
            id="header-cart-btn"
            onClick={openCart}
            className="relative bg-slate-800 hover:bg-slate-700 text-slate-100 p-2.5 rounded-xl border border-slate-700 transition-colors flex items-center justify-center"
            title="Ver Carrinho de Compras"
          >
            <ShoppingCart className="w-5 h-5 text-slate-200" />
            {cartCount > 0 && (
              <span id="cart-badge-counter" className="absolute -top-1.5 -right-1.5 bg-cyan-500 text-slate-950 font-extrabold text-[11px] w-5 h-5 rounded-full flex items-center justify-center border-2 border-slate-900 shadow-sm">
                {cartCount}
              </span>
            )}
          </button>

          <div id="user-profile-badge" className="hidden sm:flex items-center space-x-2 bg-slate-800/80 px-2.5 py-1.5 rounded-xl border border-slate-700/80">
            <div className="w-7 h-7 rounded-lg bg-teal-600/30 text-teal-300 border border-teal-500/40 flex items-center justify-center font-bold text-xs">
              <User className="w-4 h-4" />
            </div>
            <div className="text-left leading-tight hidden lg:block">
              <span className="text-xs font-semibold text-slate-200 block">Oficina Central</span>
              <span className="text-[10px] text-teal-400 font-mono block">CNPJ 48.102.392/0001</span>
            </div>
          </div>
        </div>
      </div>

      {/* Screen Switcher Bar for Quick Demonstration across all requested UI views */}
      <div id="demo-screens-switcher-bar" className="bg-slate-950 py-1.5 px-4 border-t border-slate-800/80 overflow-x-auto flex items-center justify-between text-xs">
        <span className="text-slate-400 font-medium text-[11px] whitespace-nowrap mr-2">
          Telas do App:
        </span>
        <div className="flex items-center space-x-2">
          <button
            id="switch-btn-catalog"
            onClick={() => setCurrentView('catalog')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap ${
              currentView === 'catalog' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            1. Catálogo Técnico
          </button>
          <button
            id="switch-btn-dashboard"
            onClick={() => setCurrentView('dashboard')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap ${
              currentView === 'dashboard' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            2. Dashboard Recharts
          </button>
          <button
            id="switch-btn-diagnostic"
            onClick={() => setCurrentView('diagnostic')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap ${
              currentView === 'diagnostic' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            2. Diagnóstico IA
          </button>
          <button
            id="switch-btn-product-detail"
            onClick={() => setCurrentView('product_detail')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap ${
              currentView === 'product_detail' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            3. Detalhes da Peça
          </button>
          <button
            id="switch-btn-cart"
            onClick={() => setCurrentView('cart_checkout')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap ${
              currentView === 'cart_checkout' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            4. Carrinho & Checkout
          </button>
          <button
            id="switch-btn-tickets"
            onClick={() => setCurrentView('tickets')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap ${
              currentView === 'tickets' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            5. Chamados
          </button>
          <button
            id="switch-btn-admin-manuals"
            onClick={() => setCurrentView('admin_manuals')}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap ${
              currentView === 'admin_manuals' ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            6. Fila de Manuais (Admin)
          </button>
        </div>
      </div>
    </header>
  );
};
