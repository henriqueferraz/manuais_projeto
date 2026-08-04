import { Product, Ticket, ManualReview, ChatMessage } from '../types';

export const MOCK_PRODUCTS: Product[] = [
  {
    id: 'prod-1',
    sku: 'HEL-MON-VTE40',
    name: 'Hélice Mondial VTE-02 Black 40cm (6 Pás)',
    brand: 'Mondial',
    category: 'partes',
    price: 44.90,
    oldPrice: 59.90,
    rating: 4.8,
    reviewsCount: 128,
    inStock: true,
    voltage: 'Bivolt',
    badge: 'COMPATIBILIDADE GARANTIDA',
    image: 'https://images.unsplash.com/photo-1615880484746-a134be9a6ecf?auto=format&fit=crop&w=600&q=80',
    description: 'Hélice de reposição de alta durabilidade com design aerodinâmico silencioso de 6 pás para ventiladores de teto e coluna Mondial 40cm.',
    specs: {
      material: 'Polipropileno Virgem de Alta Resistência',
      diameter: '40 cm',
      blades: '6 pás aerodinâmicas',
      mountingHole: '8 mm com trava de eixo',
      color: 'Preto Fosco Antistático',
      weight: '320g'
    },
    compatibleModels: ['VT-41-6P', 'VTE-02', 'V-40-6P', 'NV-15-6P', 'V-45'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    id: 'prod-2',
    sku: 'MOT-EMB-14R134',
    name: 'Motor Compressor 1/4 HP R134a 110V',
    brand: 'Embraco',
    category: 'motores',
    price: 389.00,
    oldPrice: 429.00,
    rating: 4.9,
    reviewsCount: 84,
    inStock: true,
    voltage: '110v',
    badge: 'TECNOLOGIA INVERTER',
    image: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=600&q=80',
    description: 'Compressor hermético Embraco de alta eficiência para refrigeração comercial e doméstica com fluido ecológico R134a.',
    specs: {
      power: '1/4 HP',
      voltage: '110V / 60Hz',
      refrigerant: 'R134a',
      material: 'Aço liga e bobinagem de cobre puro',
      weight: '8.4kg'
    },
    compatibleModels: ['EMBRACO-EGAS70', 'FFI7.5HAK', 'REFR-BRASTEMP-350', 'CONSUL-CRD36'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    id: 'prod-3',
    sku: 'PLC-INV-SMRT80',
    name: 'Placa Interface Inverter Smart Control',
    brand: 'SmartControl',
    category: 'componentes',
    price: 185.50,
    oldPrice: 210.00,
    rating: 4.7,
    reviewsCount: 56,
    inStock: true,
    voltage: '220v',
    badge: 'PREFERIDO PELA IA',
    image: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80',
    description: 'Módulo eletrônico microprocessado de controle de fase e frequência para motores inverter trifásicos e compressores variáveis.',
    specs: {
      voltage: '220V AC',
      material: 'FR-4 Dupla Camada com Verniz Protetor',
      mountingHole: 'Padrão DIN 35mm',
      weight: '190g'
    },
    compatibleModels: ['INV-SMART-2024', 'SPLIT-INVERTER-18K', 'X-SERVO-2024'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    id: 'prod-4',
    sku: 'HEL-IND-BAL60',
    name: 'Conjunto Hélice 60cm Balanceada Industrial',
    brand: 'Ventilac',
    category: 'hvac',
    price: 142.00,
    oldPrice: 168.00,
    rating: 4.9,
    reviewsCount: 37,
    inStock: true,
    voltage: 'Bivolt',
    badge: 'FLUXO OTIMIZADO',
    image: 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?auto=format&fit=crop&w=600&q=80',
    description: 'Conjunto hélice industrial em alumínio fundido balanceado dinamicamente para alta vazão com baixo nível de ruído em exaustores.',
    specs: {
      material: 'Alumínio Fundido Aeronáutico',
      diameter: '60 cm',
      blades: '4 pás simétricas',
      mountingHole: 'Eixo 1/2 polegada',
      weight: '1.2kg'
    },
    compatibleModels: ['V-400-INDUSTRIAL', 'EXAUST-60-IND', 'TURBO-IND-200'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    id: 'prod-5',
    sku: 'SKU-CAP-45UF',
    name: 'Capacitor Permanente de Partida 45uF 450V',
    brand: 'Epcos / TDK',
    category: 'componentes',
    price: 84.90,
    rating: 4.9,
    reviewsCount: 210,
    inStock: true,
    voltage: '220v',
    badge: 'PREFERIDO PELA IA',
    image: 'https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80',
    description: 'Capacitor de filme de polipropileno metalizado autorregenerativo para partida e funcionamento continuo de motores elétricos.',
    specs: {
      material: 'Alumínio cilíndrico com resina poliuretano',
      voltage: '450V AC 50/60Hz',
      diameter: '50mm x 100mm',
      weight: '140g'
    },
    compatibleModels: ['V-400-INDUSTRIAL', 'MOTOR-TRIF-1LE1', 'COMP-EMBRACO-14'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    id: 'prod-6',
    sku: 'SKU-FUS-135C',
    name: 'Kit Fusível Térmico 135°C 10A (Pacote com 5un)',
    brand: 'NTP Tech',
    category: 'componentes',
    price: 22.50,
    rating: 4.8,
    reviewsCount: 94,
    inStock: true,
    voltage: 'Bivolt',
    badge: 'COMPATIBILIDADE GARANTIDA',
    image: 'https://images.unsplash.com/photo-1563770660941-20978e870e26?auto=format&fit=crop&w=600&q=80',
    description: 'Protetor térmico de liga eutética para desligamento imediato em sobreaquecimento de bobinas e transformadores.',
    specs: {
      material: 'Cápsula cerâmica e liga de prata',
      power: '10A / 250V AC',
      weight: '15g'
    },
    compatibleModels: ['VT-41-6P', 'VTE-02', 'V-400-INDUSTRIAL', 'MONDIAL-ALL'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    id: 'prod-7',
    sku: 'MOT-TRI-SIEM1',
    name: 'Motor Trifásico de Alta Eficiência 1LE1 2CV',
    brand: 'Siemens',
    category: 'motores',
    price: 1890.00,
    oldPrice: 2150.00,
    rating: 5.0,
    reviewsCount: 18,
    inStock: true,
    voltage: 'Trifásico',
    badge: 'TECNOLOGIA INVERTER',
    image: 'https://images.unsplash.com/photo-1581092335397-9583fe92d232?auto=format&fit=crop&w=600&q=80',
    description: 'Motor assíncrono gaiola de esquilo IE3 de eficiência premium para linhas de produção contínuas.',
    specs: {
      power: '2.0 CV / 1.5 kW',
      voltage: '220V/380V Trifásico',
      rpm: '1750 RPM',
      weight: '18.5kg'
    },
    compatibleModels: ['SIEMENS-SIMOTICS-1LE1', 'ESTEIRA-IND-500', 'POMPA-PRE-200'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  },
  {
    id: 'prod-8',
    sku: 'SNS-PRESS-XMLP',
    name: 'Sensor de Pressão Digital XMLP 0-10Bar',
    brand: 'Schneider Electric',
    category: 'sensores',
    price: 345.00,
    rating: 4.9,
    reviewsCount: 42,
    inStock: true,
    voltage: '220v',
    badge: 'PREFERIDO PELA IA',
    image: 'https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?auto=format&fit=crop&w=600&q=80',
    description: 'Transmissor de pressão piezoelétrico compacto em aço inox 316L para fluidos hidráulicos e pneumáticos.',
    specs: {
      material: 'Inox AISI 316L',
      voltage: '24V DC (Saída 4-20mA)',
      mountingHole: 'Rosca G 1/4" Macho',
      weight: '110g'
    },
    compatibleModels: ['SCHNEIDER-XMLP', 'AUT-HYDRAULIC-V4', 'CH-8842-LINE'],
    manualPdfUrl: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
  }
];

export const MOCK_INITIAL_CHAT: ChatMessage[] = [
  {
    id: 'msg-1',
    sender: 'user',
    text: 'Meu ventilador industrial V-400 não liga. Percebi um cheiro de queimado logo antes de parar.',
    timestamp: '14:22'
  },
  {
    id: 'msg-2',
    sender: 'ai',
    text: 'Analisei a descrição técnica dos sintomas do seu equipamento. O cheiro característico de esmaltamento térmico seguido de travamento indica sobrecarga na bobina auxiliar de partida.',
    timestamp: '14:22',
    responseTime: '0.8s',
    diagnosisCard: {
      title: 'DIAGNÓSTICO PRELIMINAR - SOBRECARGA NO CAPACITOR DE PARTIDA',
      confidence: 85,
      description: 'Baseado na descrição do "cheiro de queimado" e na cessação total de rotação, há 85% de probabilidade de falha no Capacitor de Partida de 45uF ou rompimento do Fusível Térmico de 135°C no estator.',
      refManual: 'REF: MANUAL V-SERIES • PÁG. 42 "Em caso de interrupção abrupta e sobreaquecimento da bobina de partida..."',
      recommendedSkus: ['SKU-CAP-45UF', 'SKU-FUS-135C']
    }
  }
];

export const MOCK_TICKETS: Ticket[] = [
  {
    id: 't-1',
    code: '#CH-8842',
    title: 'Placa Lógica - Sensor de Pressão Descalibrado',
    equipment: 'Compressor Parafuso CP-200',
    technician: 'Especialista IA Alpha',
    date: '02/08/2026',
    status: 'Em Análise',
    priority: 'Alta',
    description: 'Sinal de saída do sensor variando entre 2mA e 22mA fora da curva nominal de pressão.',
    history: [
      { date: '02/08/2026 10:15', note: 'Chamado aberto via integração de telemetria.', author: 'Sistema' },
      { date: '02/08/2026 10:20', note: 'Análise de curva de pressão sugere falha no sensor XMLP-010.', author: 'AI Specialist' }
    ]
  },
  {
    id: 't-2',
    code: '#CH-7751',
    title: 'Motor Compressor Industrial X200 - Superaquecimento',
    equipment: 'Sistema HVAC Central Bloco B',
    technician: 'Eng. Roberto Lima',
    date: '30/07/2026',
    status: 'Aguardando Peça',
    priority: 'Média',
    description: 'Temperatura da carcaça atingiu 92°C após 3 horas de ciclo continuo.',
    history: [
      { date: '30/07/2026 16:00', note: 'Aguardando chegada do kit de rolamentos selados e capacitor.', author: 'Eng. Roberto' }
    ]
  },
  {
    id: 't-3',
    code: '#CH-6120',
    title: 'Substituição Preventiva de Hélice 60cm',
    equipment: 'Exaustor Industrial Linha 03',
    technician: 'Especialista IA Beta',
    date: '25/07/2026',
    status: 'Resolvido',
    priority: 'Normal',
    description: 'Troca do conjunto de pás e balanceamento dinâmico concluídos com sucesso.',
    history: [
      { date: '25/07/2026 11:30', note: 'Pás substituídas por alumínio fundido balanceado. Teste de vibração OK.', author: 'Técnico Campo' }
    ]
  }
];

export const MOCK_MANUAL_REVIEWS: ManualReview[] = [
  {
    id: 'man-1',
    filename: 'Manual_Tecnico_Mondial_VTE_2024.pdf',
    manufacturer: 'Mondial',
    skuCode: 'HEL-MON-VTE40',
    uploadDate: '03/08/2026 09:12',
    confidence: 85,
    status: 'Aguardando Revisão',
    extractedData: {
      model: 'VTE-02 Black 40cm',
      voltage: '110V / 220V (Bivolt)',
      power: '140W',
      bearings: 'Bronze Sinterizado Autolubrificante',
      temperatureRange: '-10°C a +70°C'
    }
  },
  {
    id: 'man-2',
    filename: 'Embraco_Compressor_Series_EGAS.pdf',
    manufacturer: 'Embraco',
    skuCode: 'MOT-EMB-14R134',
    uploadDate: '02/08/2026 18:40',
    confidence: 92,
    status: 'Aprovado',
    extractedData: {
      model: 'EGAS 70 HLPR',
      voltage: '115V 60Hz',
      power: '1/4 HP Nominal',
      bearings: 'Mancal Cilíndrico de Precisão',
      temperatureRange: '-35°C a +10°C (LBP/MBP)'
    }
  },
  {
    id: 'man-3',
    filename: 'Siemens_Motors_1LE1_Datasheet.pdf',
    manufacturer: 'Siemens',
    skuCode: 'MOT-TRI-SIEM1',
    uploadDate: '01/08/2026 14:15',
    confidence: 68,
    status: 'Erro Extração',
    extractedData: {
      model: '1LE1001-1AB42',
      voltage: '220/380V Trifásico',
      power: '2.0 CV (1.5 kW)',
      bearings: 'Rolamento 6206-2ZC3',
      temperatureRange: '-20°C a +40°C (Classe F)'
    }
  }
];
