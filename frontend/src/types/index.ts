export type FieldStatus =
  | 'extracted'
  | 'needs_review'
  | 'confirmed'
  | 'missing'
  | 'conflicting'
  | 'invalid';

export type ConfirmationStatus = 'unconfirmed' | 'confirmed' | 'modified';

export interface FormTemplate {
  id: string;
  original_filename: string;
  file_type: string;
  page_count: number;
  is_fillable: boolean;
  created_at: string;
}

export interface TemplateField {
  id: string;
  template_id: string;
  field_key: string;
  label: string;
  field_type: string;
  required: boolean;
  section: string;
  page_number: number;
  bounding_box?: { x: number; y: number; width: number; height: number };
  constraints?: Record<string, any>;
}

export interface CandidateValue {
  value: string;
  source_document_id: string;
  source_document_name: string;
  source_page: number;
  confidence: number;
  rationale?: string;
}

export interface FormFieldState {
  response_id: string;
  field_id: string;
  field_key: string;
  label: string;
  field_type: string;
  required: boolean;
  section: string;
  page_number: number;
  current_value: string | null;
  source_document_id: string | null;
  source_document_name: string | null;
  source_page: number | null;
  confidence: number;
  validation_status: FieldStatus;
  confirmation_status: ConfirmationStatus;
  validation_error: string | null;
  candidate_values?: CandidateValue[] | null;
}

export interface SessionMetrics {
  total_fields: number;
  confirmed_fields: number;
  extracted_fields: number;
  missing_fields: number;
  conflicting_fields: number;
  invalid_fields: number;
  completion_percentage: number;
}

export interface StylePreferences {
  font_family?: string;
  font_size?: number;
  text_color?: string;
}

export interface FormSession {
  id: string;
  template_id: string;
  title: string;
  status: 'draft' | 'processing' | 'in_progress' | 'awaiting_review' | 'completed' | 'failed';
  completion_percentage: number;
  current_stage: string;
  generated_document_path: string | null;
  signature_path?: string | null;
  style_preferences?: StylePreferences | null;
  created_at: string;
  updated_at: string;
  metrics?: SessionMetrics;
  fields?: FormFieldState[];
  documents?: UploadedDoc[];
  template?: FormTemplate;
}

export interface UploadedDoc {
  id: string;
  session_id?: string;
  filename: string;
  file_type: string;
  file_size: number;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  message: string;
  suggested_replies?: string[] | null;
  updated_field_ids?: string[] | null;
  created_at: string;
}
