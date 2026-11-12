import type { NavItem } from "./navConfig";

export function isNavItemActive(pathname: string, search: string, item: NavItem): boolean {
  if (item.to === "/" || (item.end && item.to === "/")) {
    return pathname === "/";
  }
  if (item.to.includes("status=under_review")) {
    return pathname === "/claims" && search.includes("status=under_review");
  }
  if (item.to === "/claims") {
    return pathname === "/claims" && !search.includes("status=under_review");
  }
  if (item.to === "/claims/new") {
    return pathname === "/claims/new";
  }
  if (item.to === "/admin") {
    return pathname === "/admin" || pathname.startsWith("/admin/");
  }
  const [path] = item.to.split("?");
  return pathname === path;
}
