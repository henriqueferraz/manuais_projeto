import React, { useState } from 'react';
import { CartItem } from '../types';
import {
  ShoppingCart,
  ShieldCheck,
  Truck,
  CreditCard,
  QrCode,
  FileText,
  Trash2,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Lock,
  Tag
} from 'lucide-react';

interface CartCheckoutViewProps {
  cartItems: CartItem[];
  onUpdateQuantity: (productId: string, quantity: number) => void;
  onRemoveItem: (productId: string) => void;
  onClearCart: () => void;
  onCompleteOrder: () => void;
}

export const CartCheckoutView: React.FC<CartCheckoutViewProps> = ({
  cartItems,
  onUpdateQuantity,
  onRemoveItem,
  onClearCart,
  onCompleteOrder
}) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [shippingOption, setShippingOption] = useState<'express' | 'standard'>('express');
  const [paymentMethod, setPaymentMethod] = useState<'credit' | 'pix' | 'boleto'>('credit');
  const [coupon, setCoupon] = useState('');
  const [couponDiscount, setCouponDiscount] = useState(0);

  // Credit Card Form
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvv, setCardCvv] = useState('');
  const [installments, setInstallments] = useState('1');

  const subtotal = cartItems.reduce((acc, item) => acc + item.product.price * item.quantity, 0);
  const freight = cartItems.length > 0 ? (shippingOption === 'express' ? 45.00 : 12.90) : 0;
  const pixDiscount = paymentMethod === 'pix' ? subtotal * 0.05 : 0;
  const total = Math.max(0, subtotal + freight - couponDiscount - pixDiscount);

  const handleApplyCoupon = (e: React.FormEvent) => {
    e.preventDefault();
    if (coupon.trim().toUpperCase() === 'TECH10') {
      setCouponDiscount(subtotal * 0.10);
      alert('Cupom TECH10 aplicado com sucesso! 10% de desconto.');
    } else {
      alert('Cupom inválido. Tente TECH10');
    }
  };

  return (
    <div id="cart-checkout-root" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Checkout Progress Steps */}
      <div id="checkout-progress-bar" className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
        {[
          { num: 1, label: '1. Carrinho & Itens' },
          { num: 2, label: '2. Frete Expresso' },
          { num: 3, label: '3. Pagamento Seguro' }
        ].map((s) => (
          <button
            key={s.num}
            onClick={() => setStep(s.num as any)}
            className={`flex items-center space-x-2 text-xs sm:text-sm font-bold transition-all ${
              step === s.num
                ? 'text-cyan-600 font-extrabold border-b-2 border-cyan-600 pb-1'
                : step > s.num
                ? 'text-teal-600 font-semibold'
                : 'text-slate-400'
            }`}
          >
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
              step === s.num ? 'bg-cyan-600 text-white' : step > s.num ? 'bg-teal-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>
              {step > s.num ? '✓' : s.num}
            </div>
            <span>{s.label}</span>
          </button>
        ))}
      </div>

      {/* AI Compatibility Summary Alert */}
      <div id="ai-cart-compatibility-alert" className="bg-slate-900 text-white p-4 rounded-2xl border border-slate-800 flex items-start space-x-3 shadow-md">
        <Sparkles className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5 text-xs">
          <h4 className="font-bold text-slate-100 flex items-center gap-2">
            Análise de Compatibilidade Ativa
            <span className="bg-teal-950 text-teal-300 text-[10px] font-mono px-2 py-0.5 rounded border border-teal-800">
              100% COMPATÍVEL
            </span>
          </h4>
          <p className="text-slate-300">
            Identificamos que todos os componentes no seu carrinho pertencem à mesma especificação de tolerância. Recomendamos o frete expresso para evitar paradas na sua linha de produção.
          </p>
        </div>
      </div>

      {cartItems.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-3xl border border-slate-200 shadow-sm space-y-4">
          <ShoppingCart className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-lg font-bold text-slate-800">Seu carrinho está vazio</h3>
          <p className="text-xs text-slate-500">Navegue pelo catálogo e adicione os componentes necessários.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content Area (Items / Shipping / Payment) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Step 1: Items List */}
            {step === 1 && (
              <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h3 className="font-bold text-slate-900 text-base">Itens Selecionados ({cartItems.length})</h3>
                  <button onClick={onClearCart} className="text-xs text-red-500 hover:underline font-semibold">
                    Esvaziar Carrinho
                  </button>
                </div>

                <div className="space-y-4">
                  {cartItems.map((item) => (
                    <div
                      key={item.product.id}
                      className="flex items-center gap-4 p-4 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                    >
                      <img
                        src={item.product.image}
                        alt={item.product.name}
                        referrerPolicy="no-referrer"
                        className="w-16 h-16 object-cover rounded-xl border border-slate-200 flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0 space-y-1">
                        <span className="text-[10px] font-mono text-slate-400 uppercase">{item.product.sku}</span>
                        <h4 className="font-bold text-xs text-slate-900 truncate">{item.product.name}</h4>
                        <span className="text-xs font-black text-slate-800 block">
                          R$ {item.product.price.toFixed(2).replace('.', ',')}
                        </span>
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center border border-slate-300 rounded-lg bg-white">
                        <button
                          onClick={() => onUpdateQuantity(item.product.id, item.quantity - 1)}
                          className="px-2 py-1 font-bold text-slate-600 hover:bg-slate-100"
                        >
                          -
                        </button>
                        <span className="px-3 text-xs font-bold text-slate-900">{item.quantity}</span>
                        <button
                          onClick={() => onUpdateQuantity(item.product.id, item.quantity + 1)}
                          className="px-2 py-1 font-bold text-slate-600 hover:bg-slate-100"
                        >
                          +
                        </button>
                      </div>

                      <button
                        onClick={() => onRemoveItem(item.product.id)}
                        className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>

                <div className="pt-4 text-right">
                  <button
                    onClick={() => setStep(2)}
                    className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-6 py-3 rounded-xl text-xs sm:text-sm inline-flex items-center space-x-2 shadow-sm transition-all"
                  >
                    <span>Avançar para Frete</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Shipping Options */}
            {step === 2 && (
              <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-6">
                <h3 className="font-bold text-slate-900 text-base border-b border-slate-100 pb-3 flex items-center gap-2">
                  <Truck className="w-5 h-5 text-cyan-600" />
                  Opções de Frete & Entrega Industrial
                </h3>

                <div className="space-y-3">
                  <label
                    onClick={() => setShippingOption('express')}
                    className={`p-4 rounded-2xl border-2 flex items-center justify-between cursor-pointer transition-all ${
                      shippingOption === 'express'
                        ? 'border-cyan-500 bg-cyan-50/30'
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <input type="radio" checked={shippingOption === 'express'} readOnly className="text-cyan-600" />
                      <div>
                        <div className="font-bold text-xs text-slate-900">Expresso LogiTech (24h a 48h)</div>
                        <div className="text-[11px] text-slate-500">Entrega garantida para paradas emergenciais de linha</div>
                      </div>
                    </div>
                    <span className="font-black text-xs text-slate-900">R$ 45,00</span>
                  </label>

                  <label
                    onClick={() => setShippingOption('standard')}
                    className={`p-4 rounded-2xl border-2 flex items-center justify-between cursor-pointer transition-all ${
                      shippingOption === 'standard'
                        ? 'border-cyan-500 bg-cyan-50/30'
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <input type="radio" checked={shippingOption === 'standard'} readOnly className="text-cyan-600" />
                      <div>
                        <div className="font-bold text-xs text-slate-900">Standard Econômico (5 a 7 dias)</div>
                        <div className="text-[11px] text-slate-500">Envio convencional via transportadora técnica</div>
                      </div>
                    </div>
                    <span className="font-black text-xs text-slate-900">R$ 12,90</span>
                  </label>
                </div>

                <div className="flex justify-between pt-4">
                  <button onClick={() => setStep(1)} className="text-xs font-bold text-slate-600 hover:underline">
                    Voltar aos Itens
                  </button>
                  <button
                    onClick={() => setStep(3)}
                    className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-6 py-3 rounded-xl text-xs sm:text-sm inline-flex items-center space-x-2 shadow-sm transition-all"
                  >
                    <span>Avançar para Pagamento</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Payment Method */}
            {step === 3 && (
              <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-6">
                <h3 className="font-bold text-slate-900 text-base border-b border-slate-100 pb-3 flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-cyan-600" />
                  Método de Pagamento
                </h3>

                {/* Tabs */}
                <div className="grid grid-cols-3 gap-2 bg-slate-100 p-1 rounded-xl text-xs font-bold">
                  <button
                    onClick={() => setPaymentMethod('credit')}
                    className={`py-2 rounded-lg transition-all ${
                      paymentMethod === 'credit' ? 'bg-slate-900 text-cyan-300 shadow-sm' : 'text-slate-600'
                    }`}
                  >
                    Cartão de Crédito
                  </button>
                  <button
                    onClick={() => setPaymentMethod('pix')}
                    className={`py-2 rounded-lg transition-all ${
                      paymentMethod === 'pix' ? 'bg-slate-900 text-cyan-300 shadow-sm' : 'text-slate-600'
                    }`}
                  >
                    Pix (5% OFF)
                  </button>
                  <button
                    onClick={() => setPaymentMethod('boleto')}
                    className={`py-2 rounded-lg transition-all ${
                      paymentMethod === 'boleto' ? 'bg-slate-900 text-cyan-300 shadow-sm' : 'text-slate-600'
                    }`}
                  >
                    Boleto Bancário
                  </button>
                </div>

                {/* Credit Card Form */}
                {paymentMethod === 'credit' && (
                  <div className="space-y-4 pt-2">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Número do Cartão</label>
                      <input
                        type="text"
                        value={cardNumber}
                        onChange={(e) => setCardNumber(e.target.value)}
                        placeholder="0000 0000 0000 0000"
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded-xl p-3 focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Validade</label>
                        <input
                          type="text"
                          value={cardExpiry}
                          onChange={(e) => setCardExpiry(e.target.value)}
                          placeholder="MM/AA"
                          className="w-full bg-slate-50 border border-slate-200 text-xs rounded-xl p-3 focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-slate-700 uppercase mb-1">CVV</label>
                        <input
                          type="text"
                          value={cardCvv}
                          onChange={(e) => setCardCvv(e.target.value)}
                          placeholder="123"
                          className="w-full bg-slate-50 border border-slate-200 text-xs rounded-xl p-3 focus:outline-none focus:border-cyan-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Parcelamento</label>
                      <select
                        value={installments}
                        onChange={(e) => setInstallments(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded-xl p-3 focus:outline-none focus:border-cyan-500 font-medium"
                      >
                        <option value="1">1x de R$ {total.toFixed(2).replace('.', ',')} sem juros</option>
                        <option value="2">2x de R$ {(total / 2).toFixed(2).replace('.', ',')} sem juros</option>
                        <option value="3">3x de R$ {(total / 3).toFixed(2).replace('.', ',')} sem juros</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Pix View */}
                {paymentMethod === 'pix' && (
                  <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-center space-y-3">
                    <QrCode className="w-16 h-16 text-slate-800 mx-auto" />
                    <h4 className="font-bold text-xs text-slate-900">Aprovação Imediata no Pix com 5% de Desconto</h4>
                    <p className="text-[11px] text-slate-500">O código QR será gerado na próxima tela após a confirmação.</p>
                  </div>
                )}

                {/* Boleto View */}
                {paymentMethod === 'boleto' && (
                  <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 text-center space-y-3">
                    <FileText className="w-12 h-12 text-slate-800 mx-auto" />
                    <h4 className="font-bold text-xs text-slate-900">Boleto Bancário Faturado para Pessoas Jurídicas</h4>
                    <p className="text-[11px] text-slate-500">Vencimento em 3 dias úteis. Compensação em até 24h.</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Column: Order Summary Box */}
          <div className="space-y-6">
            <div className="bg-slate-900 text-white p-6 rounded-3xl border border-slate-800 shadow-xl space-y-5">
              <h3 className="font-bold text-base border-b border-slate-800 pb-3 flex items-center justify-between">
                <span>Resumo do Pedido</span>
                <Lock className="w-4 h-4 text-teal-400" />
              </h3>

              {/* Coupon Form */}
              <form onSubmit={handleApplyCoupon} className="flex gap-2">
                <input
                  type="text"
                  value={coupon}
                  onChange={(e) => setCoupon(e.target.value)}
                  placeholder="Cupom (Ex: TECH10)"
                  className="flex-1 bg-slate-950 text-slate-100 text-xs rounded-xl px-3 py-2 border border-slate-700 focus:outline-none"
                />
                <button
                  type="submit"
                  className="bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold px-3 py-2 rounded-xl text-xs border border-slate-700"
                >
                  Aplicar
                </button>
              </form>

              {/* Price Table */}
              <div className="space-y-2.5 text-xs border-t border-slate-800 pt-3">
                <div className="flex justify-between text-slate-300">
                  <span>Subtotal ({cartItems.reduce((a, b) => a + b.quantity, 0)} itens)</span>
                  <span>R$ {subtotal.toFixed(2).replace('.', ',')}</span>
                </div>

                <div className="flex justify-between text-slate-300">
                  <span>Frete ({shippingOption === 'express' ? 'Expresso' : 'Standard'})</span>
                  <span>R$ {freight.toFixed(2).replace('.', ',')}</span>
                </div>

                {couponDiscount > 0 && (
                  <div className="flex justify-between text-teal-400 font-bold">
                    <span>Desconto Cupom</span>
                    <span>- R$ {couponDiscount.toFixed(2).replace('.', ',')}</span>
                  </div>
                )}

                {pixDiscount > 0 && (
                  <div className="flex justify-between text-teal-400 font-bold">
                    <span>Desconto Pix (5%)</span>
                    <span>- R$ {pixDiscount.toFixed(2).replace('.', ',')}</span>
                  </div>
                )}

                <div className="flex justify-between text-base font-black text-white pt-2 border-t border-slate-800">
                  <span>Total</span>
                  <span className="text-cyan-400">R$ {total.toFixed(2).replace('.', ',')}</span>
                </div>
              </div>

              {/* Finalize Button */}
              <button
                onClick={onCompleteOrder}
                className="w-full bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-extrabold py-3.5 px-4 rounded-2xl text-sm shadow-lg shadow-cyan-950/40 transition-all cursor-pointer flex items-center justify-center space-x-2"
              >
                <span>FINALIZAR COMPRA</span>
                <ArrowRight className="w-4 h-4 text-slate-950" />
              </button>

              <p className="text-[10px] text-slate-400 text-center flex items-center justify-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
                <span>Ambiente 100% Criptografado & Garantia TechParts AI</span>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
