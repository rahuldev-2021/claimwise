export type AuthUser = {
  user_id: string;
  email: string;
  org_id: string;
  org_name: string;
  roles: string[];
  permissions: string[];
  status: string;
};
