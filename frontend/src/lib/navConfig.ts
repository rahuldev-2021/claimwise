import type { LucideIcon } from "lucide-react";
import { FolderOpen, Home, Plus } from "lucide-react";

export type NavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
  badge?: number;
};

export type NavSection = {
  title?: string;
  items: NavItem[];
};

export type NavOptions = {
  myClaimsCount?: number;
};

export const NEW_CLAIM_PATH = "/claims/new";
export const HOME_PATH = "/";

export function appNavSections(options: NavOptions = {}): NavSection[] {
  const { myClaimsCount } = options;

  const items: NavItem[] = [
    {
      to: HOME_PATH,
      label: "Home",
      icon: Home,
      end: true,
    },
    {
      to: NEW_CLAIM_PATH,
      label: "New claim",
      icon: Plus,
    },
    {
      to: "/claims",
      label: "My claims",
      icon: FolderOpen,
      badge: myClaimsCount,
      end: true,
    },
  ];

  return [{ items }];
}
