import React, { useState } from 'react';
import { Product } from '../types';
import {
  Image as ImageIcon,
  Copy,
  Check,
  Code,
  ExternalLink,
  Download,
  X,
  Sparkles
} from 'lucide-react';

interface ImageLinksModalProps {
  products: Product[];
  onClose: () => void;
}

export const ImageLinksModal: React.FC<ImageLinksModalProps> = ({ products, onClose }) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div id="image-links-modal-overlay" className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 text-white max-w-3xl w-full rounded-3xl border border-slate-800 shadow-2xl p-6 sm:p-8 space-y-6 max-h-[85vh] overflow-y-auto">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center justify-center font-bold">
              <ImageIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-lg text-slate-100">Links Diretos das Imagens do HTML</h3>
              <p className="text-xs text-slate-400">Copie os URLs das imagens ou as tags HTML &lt;img&gt; prontas com referrerPolicy</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Info Banner */}
        <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 flex items-start space-x-3 text-xs text-slate-300">
          <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <p>
            Todas as imagens são servidas diretamente via HTTPS e incluem a instrução <code className="bg-slate-900 text-cyan-300 px-1 py-0.5 rounded font-mono text-[11px]">referrerpolicy="no-referrer"</code> para prevenir bloqueios de renderização.
          </p>
        </div>

        {/* Images List */}
        <div className="space-y-4">
          {products.map((p) => {
            const htmlTag = `<img src="${p.image}" alt="${p.name}" referrerpolicy="no-referrer" />`;
            const isUrlCopied = copiedId === `url-${p.id}`;
            const isTagCopied = copiedId === `tag-${p.id}`;

            return (
              <div
                key={p.id}
                className="bg-slate-950 p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center gap-4 hover:border-slate-700 transition-colors"
              >
                {/* Thumbnail */}
                <div className="w-16 h-16 rounded-xl bg-slate-900 border border-slate-800 overflow-hidden flex-shrink-0">
                  <img src={p.image} alt={p.name} referrerPolicy="no-referrer" className="w-full h-full object-cover" />
                </div>

                {/* Information */}
                <div className="flex-1 min-w-0 space-y-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[10px] text-cyan-400 font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                      SKU: {p.sku}
                    </span>
                    <h4 className="font-bold text-xs text-slate-100 truncate">{p.name}</h4>
                  </div>

                  <div className="font-mono text-[11px] text-slate-400 truncate bg-slate-900/80 p-2 rounded-lg border border-slate-800/80">
                    {p.image}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
                  <button
                    onClick={() => copyToClipboard(p.image, `url-${p.id}`)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-3 py-1.5 rounded-lg text-xs flex items-center space-x-1 border border-slate-700 transition-colors"
                    title="Copiar apenas o Link da Imagem"
                  >
                    {isUrlCopied ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{isUrlCopied ? 'Copiado!' : 'Copiar URL'}</span>
                  </button>

                  <button
                    onClick={() => copyToClipboard(htmlTag, `tag-${p.id}`)}
                    className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs flex items-center space-x-1 shadow-sm transition-colors"
                    title="Copiar tag HTML <img /> completa"
                  >
                    {isTagCopied ? <Check className="w-3.5 h-3.5 text-slate-950" /> : <Code className="w-3.5 h-3.5 text-slate-950" />}
                    <span>{isTagCopied ? 'Tag Copiada!' : 'Tag HTML'}</span>
                  </button>

                  <a
                    href={p.image}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 text-slate-400 hover:text-white bg-slate-800 rounded-lg"
                    title="Abrir imagem em nova aba"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer actions */}
        <div className="flex justify-end pt-2 border-t border-slate-800">
          <button
            onClick={onClose}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold px-5 py-2 rounded-xl text-xs"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};
