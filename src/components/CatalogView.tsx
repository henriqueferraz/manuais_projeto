import React, { useState } from 'react';
import { Product } from '../types';
import {
  SlidersHorizontal,
  CheckCircle2,
  Star,
  ShoppingCart,
  Headphones,
  Check,
  ChevronRight,
  Zap,
  Tag,
  Eye,
  Sparkles
} from 'lucide-react';

interface CatalogViewProps {
  products: Product[];
  onSelectProduct: (product: Product) => void;
  onAddToCart: (product: Product) => void;
  onOpenConsultant: () => void;
}

export const CatalogView: React.FC<CatalogViewProps> = ({
  products,
  onSelectProduct,
  onAddToCart,
  onOpenConsultant
}) => {
  const [selectedBrand, setSelectedBrand] = useState('Todas');
  const [selectedVoltage, setSelectedVoltage] = useState('Todas');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [addedProductIds, setAddedProductIds] = useState<Record<string, boolean>>({});

  const toggleCategory = (cat: string) => {
    if (selectedCategories.includes(cat)) {
      setSelectedCategories(selectedCategories.filter(c => c !== cat));
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
  };

  const handleAddToCart = (e: React.MouseEvent, product: Product) => {
    e.stopPropagation();
    onAddToCart(product);
    setAddedProductIds(prev => ({ ...prev, [product.id]: true }));
    setTimeout(() => {
      setAddedProductIds(prev => ({ ...prev, [product.id]: false }));
    }, 1500);
  };

  const filteredProducts = products.filter(p => {
    if (selectedBrand !== 'Todas' && p.brand.toLowerCase() !== selectedBrand.toLowerCase()) {
      return false;
    }
    if (selectedVoltage !== 'Todas') {
      if (selectedVoltage === '110v' && p.voltage !== '110v' && p.voltage !== 'Bivolt') return false;
      if (selectedVoltage === '220v' && p.voltage !== '220v' && p.voltage !== 'Bivolt') return false;
    }
    if (selectedCategories.length > 0) {
      if (!selectedCategories.includes(p.category)) return false;
    }
    return true;
  });

  return (
    <div id="catalog-view-root" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Filter Sidebar */}
        <aside id="catalog-filter-sidebar" className="lg:col-span-1 space-y-6">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-cyan-600" />
                Filtros Técnicos
              </h3>
              {(selectedBrand !== 'Todas' || selectedVoltage !== 'Todas' || selectedCategories.length > 0) && (
                <button
                  id="reset-filters-btn"
                  onClick={() => {
                    setSelectedBrand('Todas');
                    setSelectedVoltage('Todas');
                    setSelectedCategories([]);
                  }}
                  className="text-[11px] text-cyan-600 font-semibold hover:underline"
                >
                  Limpar
                </button>
              )}
            </div>

            {/* Brand Dropdown */}
            <div id="filter-brand-group">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Marca do Equipamento
              </label>
              <select
                id="filter-brand-select"
                value={selectedBrand}
                onChange={(e) => setSelectedBrand(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 text-slate-800 text-xs rounded-xl p-2.5 font-medium focus:outline-none focus:border-cyan-500 focus:bg-white transition-all cursor-pointer"
              >
                <option value="Todas">Todas as Marcas (Mondial, Embraco, Siemens, Schneider...)</option>
                <option value="Mondial">Mondial</option>
                <option value="Embraco">Embraco</option>
                <option value="Siemens">Siemens</option>
                <option value="Schneider">Schneider Electric</option>
                <option value="SmartControl">SmartControl</option>
              </select>
            </div>

            {/* Voltage Tabs */}
            <div id="filter-voltage-group">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Tensão Elétrica
              </label>
              <div className="grid grid-cols-3 gap-1.5 bg-slate-100 p-1 rounded-xl">
                {['Todas', '110v', '220v'].map((v) => (
                  <button
                    key={v}
                    id={`filter-voltage-${v}`}
                    onClick={() => setSelectedVoltage(v)}
                    className={`py-1.5 text-xs font-bold rounded-lg transition-all ${
                      selectedVoltage === v
                        ? 'bg-slate-900 text-cyan-300 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>

            {/* Category Checkboxes */}
            <div id="filter-category-group">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Categoria de Peça
              </label>
              <div className="space-y-2.5">
                {[
                  { id: 'componentes', label: 'Componentes Eletrônicos' },
                  { id: 'motores', label: 'Motores & Compressores' },
                  { id: 'partes', label: 'Partes Estruturais & Hélices' },
                  { id: 'sensores', label: 'Sensores de Precisão' },
                  { id: 'hvac', label: 'Linha HVAC & Exaustores' }
                ].map((cat) => {
                  const isChecked = selectedCategories.includes(cat.id);
                  return (
                    <label
                      key={cat.id}
                      className="flex items-center space-x-2.5 text-xs font-medium text-slate-700 hover:text-slate-900 cursor-pointer select-none"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleCategory(cat.id)}
                        className="rounded border-slate-300 text-cyan-600 focus:ring-cyan-500 w-4 h-4 cursor-pointer"
                      />
                      <span>{cat.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Technical Support Box */}
          <div id="tech-support-sidebar-card" className="bg-gradient-to-br from-slate-900 to-slate-950 p-5 rounded-2xl border border-slate-800 text-white shadow-md space-y-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center justify-center">
              <Headphones className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-slate-100">Consultoria Técnica Direta</h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Dúvidas sobre o SKU exato, folga mecânica ou curva de pressão do seu equipamento?
              </p>
            </div>
            <button
              id="open-consultant-btn"
              onClick={onOpenConsultant}
              className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center space-x-2 shadow-md transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-slate-950" />
              <span>Consultar Técnico IA</span>
            </button>
          </div>
        </aside>

        {/* Main Catalog Content */}
        <main id="catalog-main-content" className="lg:col-span-3 space-y-8">
          
          {/* Featured Categories Row */}
          <div id="featured-categories-row" className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-5 rounded-2xl border border-slate-700/80 text-white relative overflow-hidden flex items-center justify-between shadow-md">
              <div className="relative z-10 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800">
                  Alta Demanda
                </span>
                <h3 className="text-lg font-bold">Linha HVAC & Ventilação</h3>
                <p className="text-xs text-slate-300">Hélices balanceadas, capacitores e protetores térmicos</p>
              </div>
              <div className="w-12 h-12 bg-cyan-500/10 rounded-2xl border border-cyan-500/30 flex items-center justify-center text-cyan-400 flex-shrink-0">
                <Zap className="w-6 h-6" />
              </div>
            </div>

            <div className="bg-gradient-to-r from-teal-950 to-slate-900 p-5 rounded-2xl border border-teal-800/60 text-white relative overflow-hidden flex items-center justify-between shadow-md">
              <div className="relative z-10 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-300 bg-teal-950/80 px-2 py-0.5 rounded border border-teal-800">
                  Linha Inverter
                </span>
                <h3 className="text-lg font-bold">Compressores & Sensores</h3>
                <p className="text-xs text-slate-300">R134a e transmissores de pressão 4-20mA</p>
              </div>
              <div className="w-12 h-12 bg-teal-500/10 rounded-2xl border border-teal-500/30 flex items-center justify-center text-teal-300 flex-shrink-0">
                <Tag className="w-6 h-6" />
              </div>
            </div>
          </div>

          {/* Catalog Section Header */}
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Produtos em Destaque</h2>
              <p className="text-xs text-slate-500">Exibindo {filteredProducts.length} itens com garantia de compatibilidade</p>
            </div>
            <div className="text-xs text-slate-500 font-medium">
              Ordenado por: <span className="font-bold text-slate-800">Mais Relevantes (IA)</span>
            </div>
          </div>

          {/* Product Grid */}
          <div id="product-grid" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProducts.map((product) => {
              const isAdded = addedProductIds[product.id];
              return (
                <div
                  key={product.id}
                  id={`product-card-${product.id}`}
                  onClick={() => onSelectProduct(product)}
                  className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer flex flex-col justify-between group"
                >
                  <div>
                    {/* Image Box */}
                    <div className="relative bg-slate-100 aspect-square overflow-hidden flex items-center justify-center p-4">
                      {product.badge && (
                        <span className="absolute top-3 left-3 bg-slate-900 text-cyan-300 text-[10px] font-extrabold px-2.5 py-1 rounded-md shadow-md border border-slate-700 tracking-wide z-10">
                          {product.badge}
                        </span>
                      )}
                      <img
                        src={product.image}
                        alt={product.name}
                        referrerPolicy="no-referrer"
                        className="w-full h-full object-cover rounded-xl group-hover:scale-105 transition-transform duration-500"
                      />
                    </div>

                    {/* Content Box */}
                    <div className="p-4 space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                        <span>SKU: {product.sku}</span>
                        <span className="font-semibold text-slate-700">{product.brand}</span>
                      </div>

                      <h3 className="font-bold text-slate-900 text-sm line-clamp-2 group-hover:text-cyan-700 transition-colors">
                        {product.name}
                      </h3>

                      {/* Rating */}
                      <div className="flex items-center space-x-1">
                        <div className="flex text-amber-400">
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} className="w-3.5 h-3.5 fill-current" />
                          ))}
                        </div>
                        <span className="text-xs font-bold text-slate-700 ml-1">{product.rating}</span>
                        <span className="text-[11px] text-slate-400">({product.reviewsCount})</span>
                      </div>
                    </div>
                  </div>

                  {/* Footer & Price */}
                  <div className="p-4 pt-0 space-y-3">
                    <div className="flex items-baseline space-x-2">
                      <span className="text-lg font-black text-slate-900 font-sans">
                        R$ {product.price.toFixed(2).replace('.', ',')}
                      </span>
                      {product.oldPrice && (
                        <span className="text-xs text-slate-400 line-through">
                          R$ {product.oldPrice.toFixed(2).replace('.', ',')}
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectProduct(product);
                        }}
                        className="w-full bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold py-2 rounded-xl text-xs flex items-center justify-center space-x-1 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-600" />
                        <span>Ver Peça</span>
                      </button>

                      <button
                        onClick={(e) => handleAddToCart(e, product)}
                        className={`w-full font-bold py-2 rounded-xl text-xs flex items-center justify-center space-x-1 transition-all ${
                          isAdded
                            ? 'bg-teal-600 text-white'
                            : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-sm'
                        }`}
                      >
                        {isAdded ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Adicionado!</span>
                          </>
                        ) : (
                          <>
                            <ShoppingCart className="w-3.5 h-3.5" />
                            <span>Comprar</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
};
