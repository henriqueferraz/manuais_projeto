import React, { useState } from 'react';
import { ViewMode, Product, CartItem, ChatMessage, Ticket, ManualReview } from './types';
import { MOCK_PRODUCTS, MOCK_INITIAL_CHAT, MOCK_TICKETS, MOCK_MANUAL_REVIEWS } from './data/mockData';
import { Header } from './components/Header';
import { HeroSection } from './components/HeroSection';
import { CatalogView } from './components/CatalogView';
import { DiagnosticChatView } from './components/DiagnosticChatView';
import { ProductDetailView } from './components/ProductDetailView';
import { CartCheckoutView } from './components/CartCheckoutView';
import { TicketsView } from './components/TicketsView';
import { AdminManualsView } from './components/AdminManualsView';
import { DashboardSection } from './components/DashboardSection';
import { ArchitectureView } from './components/ArchitectureView';
import { ImageLinksModal } from './components/ImageLinksModal';

export default function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('catalog');
  const [selectedProduct, setSelectedProduct] = useState<Product>(MOCK_PRODUCTS[0]);
  const [cartItems, setCartItems] = useState<CartItem[]>([
    { product: MOCK_PRODUCTS[0], quantity: 1 },
    { product: MOCK_PRODUCTS[4], quantity: 2 }
  ]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(MOCK_INITIAL_CHAT);
  const [tickets, setTickets] = useState<Ticket[]>(MOCK_TICKETS);
  const [manualReviews, setManualReviews] = useState<ManualReview[]>(MOCK_MANUAL_REVIEWS);
  const [searchQuery, setSearchQuery] = useState('');
  const [isImageLinksModalOpen, setIsImageLinksModalOpen] = useState(false);
  const [isLoadingDiagnostic, setIsLoadingDiagnostic] = useState(false);
  const [heroInitialQuery, setHeroInitialQuery] = useState('');

  // Cart operations
  const handleAddToCart = (product: Product, quantity: number = 1) => {
    setCartItems(prev => {
      const existing = prev.find(item => item.product.id === product.id);
      if (existing) {
        return prev.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prev, { product, quantity }];
    });
  };

  const handleUpdateCartQuantity = (productId: string, quantity: number) => {
    if (quantity <= 0) {
      handleRemoveCartItem(productId);
      return;
    }
    setCartItems(prev =>
      prev.map(item => (item.product.id === productId ? { ...item, quantity } : item))
    );
  };

  const handleRemoveCartItem = (productId: string) => {
    setCartItems(prev => prev.filter(item => item.product.id !== productId));
  };

  const handleBuyNow = (product: Product, quantity: number = 1) => {
    handleAddToCart(product, quantity);
    setCurrentView('cart_checkout');
  };

  // Diagnostic Assistant operations
  const handleSendMessage = async (text: string, imageBase64?: string) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      image: imageBase64
    };

    setChatMessages(prev => [...prev, userMsg]);
    setIsLoadingDiagnostic(true);

    try {
      const res = await fetch('/api/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, imageBase64 })
      });
      const data = await res.json();

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: data.text || 'Análise concluída com base nos manuais de manutenção industrial.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        responseTime: data.responseTime || '0.8s',
        diagnosisCard: data.diagnosisCard
      };

      setChatMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      const fallbackAiMsg: ChatMessage = {
        id: `ai-err-${Date.now()}`,
        sender: 'ai',
        text: 'Identificamos o padrão sintomático relatado. Recomendamos a inspeção técnica do capacitor de partida e fusível de temperatura.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        responseTime: '0.6s',
        diagnosisCard: {
          title: 'DIAGNÓSTICO TÉCNICO IA',
          confidence: 88,
          description: 'Análise de tolerância e padrão térmico para equipamentos de partida elétrica.',
          refManual: 'MANUAL V-SERIES • PÁG. 42',
          recommendedSkus: ['SKU-CAP-45UF', 'SKU-FUS-135C']
        }
      };
      setChatMessages(prev => [...prev, fallbackAiMsg]);
    } finally {
      setIsLoadingDiagnostic(false);
    }
  };

  const handleStartHeroDiagnostic = (initialQuery: string) => {
    setHeroInitialQuery(initialQuery);
    setCurrentView('diagnostic');
    handleSendMessage(initialQuery);
  };

  // Ticket creation
  const handleCreateTicket = (title: string, equipment: string, description: string) => {
    const newTicket: Ticket = {
      id: `t-${Date.now()}`,
      code: `#CH-${Math.floor(1000 + Math.random() * 9000)}`,
      title,
      equipment,
      technician: 'Especialista IA Alpha',
      date: new Date().toLocaleDateString('pt-BR'),
      status: 'Em Análise',
      priority: 'Alta',
      description,
      history: [
        {
          date: `${new Date().toLocaleDateString('pt-BR')} ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
          note: 'Chamado criado pelo cliente.',
          author: 'Cliente'
        }
      ]
    };
    setTickets(prev => [newTicket, ...prev]);
  };

  // Manual approval
  const handleApproveManual = (id: string) => {
    setManualReviews(prev =>
      prev.map(m => (m.id === id ? { ...m, status: 'Aprovado', confidence: 98 } : m))
    );
  };

  const handleUploadManual = (file: File) => {
    const newManual: ManualReview = {
      id: `man-${Date.now()}`,
      filename: file.name,
      manufacturer: 'Novo Fabricante',
      skuCode: 'SKU-EXTRAIDO-AUTO',
      uploadDate: new Date().toLocaleDateString('pt-BR'),
      confidence: 91,
      status: 'Aguardando Revisão',
      extractedData: {
        model: 'Modelo Extraído via OCR/IA',
        voltage: '220V AC',
        power: '2.5 CV',
        bearings: '6205-2RS',
        temperatureRange: '-20°C a +80°C'
      }
    };
    setManualReviews(prev => [newManual, ...prev]);
    alert(`Manual "${file.name}" enviado com sucesso e enfileirado para extração IA!`);
  };

  // Filter products by global search query if entered
  const filteredProductsBySearch = MOCK_PRODUCTS.filter(p => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      p.sku.toLowerCase().includes(q) ||
      p.brand.toLowerCase().includes(q) ||
      p.compatibleModels.some(m => m.toLowerCase().includes(q))
    );
  });

  return (
    <div id="app-root" className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      
      {/* Primary Top Header */}
      <Header
        currentView={currentView}
        setCurrentView={setCurrentView}
        cartCount={cartItems.reduce((acc, item) => acc + item.quantity, 0)}
        openCart={() => setCurrentView('cart_checkout')}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        openImageLinksModal={() => setIsImageLinksModalOpen(true)}
      />

      {/* View Content Renderer */}
      <div className="flex-1">
        {currentView === 'catalog' && (
          <>
            <HeroSection onStartDiagnostic={handleStartHeroDiagnostic} />
            <DashboardSection onOpenConsultant={() => setCurrentView('diagnostic')} />
            <CatalogView
              products={filteredProductsBySearch}
              onSelectProduct={(product) => {
                setSelectedProduct(product);
                setCurrentView('product_detail');
              }}
              onAddToCart={(product) => handleAddToCart(product, 1)}
              onOpenConsultant={() => setCurrentView('diagnostic')}
            />
          </>
        )}

        {currentView === 'dashboard' && (
          <DashboardSection onOpenConsultant={() => setCurrentView('diagnostic')} />
        )}

        {currentView === 'diagnostic' && (
          <DiagnosticChatView
            messages={chatMessages}
            onSendMessage={handleSendMessage}
            products={MOCK_PRODUCTS}
            onAddToCart={(product) => handleAddToCart(product, 1)}
            onSelectProduct={(product) => {
              setSelectedProduct(product);
              setCurrentView('product_detail');
            }}
            isLoading={isLoadingDiagnostic}
            initialQuery={heroInitialQuery}
          />
        )}

        {currentView === 'product_detail' && (
          <ProductDetailView
            product={selectedProduct}
            onBack={() => setCurrentView('catalog')}
            onAddToCart={handleAddToCart}
            onBuyNow={handleBuyNow}
          />
        )}

        {currentView === 'cart_checkout' && (
          <CartCheckoutView
            cartItems={cartItems}
            onUpdateQuantity={handleUpdateCartQuantity}
            onRemoveItem={handleRemoveCartItem}
            onClearCart={() => setCartItems([])}
            onCompleteOrder={() => {
              alert('🎉 Pedido finalizado com sucesso! Código do Pedido: #TP-98214. Emissão de NFe gerada.');
              setCartItems([]);
              setCurrentView('catalog');
            }}
          />
        )}

        {currentView === 'tickets' && (
          <TicketsView
            tickets={tickets}
            onOpenNewTicket={handleCreateTicket}
          />
        )}

        {currentView === 'admin_manuals' && (
          <AdminManualsView
            manuals={manualReviews}
            onApproveManual={handleApproveManual}
            onUploadManual={handleUploadManual}
          />
        )}

        {currentView === 'architecture' && (
          <ArchitectureView />
        )}
      </div>

      {/* Footer */}
      <footer id="app-footer" className="bg-slate-950 text-slate-400 text-xs border-t border-slate-800 py-10 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-2">
            <span className="text-base font-black text-white">TechParts<span className="text-cyan-400">.AI</span></span>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Plataforma industrial de componentes técnicos integrados a motores neurais de diagnóstico e compatibilidade fabril.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-slate-200 mb-2 uppercase tracking-wider text-[11px]">Navegação Direta</h4>
            <ul className="space-y-1 text-[11px]">
              <li><button onClick={() => setCurrentView('catalog')} className="hover:text-cyan-400">Catálogo de Componentes</button></li>
              <li><button onClick={() => setCurrentView('dashboard')} className="hover:text-cyan-400">Dashboard de Telemetria (Recharts)</button></li>
              <li><button onClick={() => setCurrentView('diagnostic')} className="hover:text-cyan-400">Assistente de Diagnóstico IA</button></li>
              <li><button onClick={() => setCurrentView('tickets')} className="hover:text-cyan-400">Chamados Técnicos</button></li>
              <li><button onClick={() => setCurrentView('admin_manuals')} className="hover:text-cyan-400">Fila de Revisão de Manuais</button></li>
              <li><button onClick={() => setCurrentView('architecture')} className="text-cyan-400 hover:underline font-bold">Arquitetura Python (Django + LangGraph)</button></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-slate-200 mb-2 uppercase tracking-wider text-[11px]">Recursos & Assets</h4>
            <ul className="space-y-1 text-[11px]">
              <li><button onClick={() => setIsImageLinksModalOpen(true)} className="text-cyan-400 hover:underline">Links Diretos Imagens HTML</button></li>
              <li><a href="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf" target="_blank" rel="noreferrer" className="hover:text-cyan-400">Download de Manuais PDF</a></li>
              <li><span className="text-slate-500">API de Telemetria v4.2</span></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-slate-200 mb-2 uppercase tracking-wider text-[11px]">Atendimento Industrial</h4>
            <p className="text-[11px] text-slate-400">Plantonista de Engenharia: 0800-770-TECH</p>
            <p className="text-[11px] text-slate-400 mt-1">Horário: Seg - Sab (07h às 22h)</p>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 pt-4 border-t border-slate-900 text-center text-[11px] text-slate-600">
          © {new Date().getFullYear()} TechParts AI. Todos os direitos reservados.
        </div>
      </footer>

      {/* Direct Image Links Modal */}
      {isImageLinksModalOpen && (
        <ImageLinksModal
          products={MOCK_PRODUCTS}
          onClose={() => setIsImageLinksModalOpen(false)}
        />
      )}
    </div>
  );
}
