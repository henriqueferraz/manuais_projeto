export type ViewMode =
  | 'catalog'
  | 'diagnostic'
  | 'product_detail'
  | 'cart_checkout'
  | 'tickets'
  | 'admin_manuals'
  | 'dashboard';

export interface Product {
  id: string;
  sku: string;
  name: string;
  brand: string;
  category: 'componentes' | 'motores' | 'partes' | 'sensores' | 'hvac';
  price: number;
  oldPrice?: number;
  rating: number;
  reviewsCount: number;
  inStock: boolean;
  voltage?: '110v' | '220v' | 'Bivolt' | 'Trifásico';
  badge?: 'COMPATIBILIDADE GARANTIDA' | 'TECNOLOGIA INVERTER' | 'FLUXO OTIMIZADO' | 'PREFERIDO PELA IA';
  image: string;
  description: string;
  specs: {
    material?: string;
    diameter?: string;
    blades?: string;
    mountingHole?: string;
    color?: string;
    weight?: string;
    voltage?: string;
    power?: string;
    rpm?: string;
    refrigerant?: string;
  };
  compatibleModels: string[];
  manualPdfUrl?: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
  selectedVoltage?: string;
}

export interface DiagnosticCardData {
  title: string;
  confidence: number;
  description: string;
  refManual: string;
  recommendedSkus: string[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  diagnosisCard?: DiagnosticCardData;
  image?: string;
  responseTime?: string;
}

export interface Ticket {
  id: string;
  code: string;
  title: string;
  equipment: string;
  technician: string;
  date: string;
  status: 'Em Análise' | 'Aguardando Peça' | 'Resolvido';
  priority: 'Alta' | 'Média' | 'Normal';
  description: string;
  history: { date: string; note: string; author: string }[];
}

export interface ManualReview {
  id: string;
  filename: string;
  manufacturer: string;
  skuCode: string;
  uploadDate: string;
  confidence: number;
  status: 'Aguardando Revisão' | 'Aprovado' | 'Erro Extração';
  extractedData: {
    model: string;
    voltage: string;
    power: string;
    bearings: string;
    temperatureRange: string;
  };
}
