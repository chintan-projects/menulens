export interface PriceVariant {
  readonly label: string;
  readonly price: number;
}

export interface ExtractedMenuItem {
  readonly dish_name: string;
  readonly description: string | null;
  readonly price: number;
  readonly price_variants: readonly PriceVariant[];
  readonly currency: string;
  readonly dietary_tags: readonly string[];
  readonly spice_level: string | null;
}

export interface ExtractedMenuSection {
  readonly section_name: string;
  readonly items: readonly ExtractedMenuItem[];
}

export interface ExtractedMenu {
  readonly restaurant_name: string;
  readonly menu_sections: readonly ExtractedMenuSection[];
  readonly extraction_notes: string | null;
}

export interface ExtractionResponse {
  readonly menu: ExtractedMenu;
  readonly confidence: number;
  readonly total_items: number;
  readonly total_sections: number;
}

export interface ExtractionRequest {
  readonly menu_text: string;
  readonly restaurant_name: string;
  readonly source_type: string;
}
