export interface CrmDeal {
  id: string;
  organization_id: string;
  title: string;
  value_amount: number;
  currency: string;
  stage: string;
  contact_id?: string;
  owner_user_id?: string;
  expected_close_date?: string;
  created_at: string;
  updated_at: string;
}
