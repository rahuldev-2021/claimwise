import { ChevronRight, LogOut, Settings, Shield } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { ThemeToggleIcon } from "./ThemeToggleIcon";
import { isAdminRole, primaryRole, roleLabel } from "../lib/roles";

function initials(email: string): string {
  const part = email.split("@")[0] ?? "U";
  return part.slice(0, 2).toUpperCase();
}

const MENU_WIDTH = 288;

export function UserAccountMenu({ collapsed }: { collapsed?: boolean }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [menuPos, setMenuPos] = useState({ left: 0, bottom: 0 });
  const role = primaryRole(user?.roles);

  const updatePosition = useCallback(() => {
    const el = buttonRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    let left = r.right + 8;
    if (left + MENU_WIDTH > window.innerWidth - 8) {
      left = Math.max(8, r.left - MENU_WIDTH - 8);
    }
    setMenuPos({ left, bottom: window.innerHeight - r.bottom });
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!open) return;
    updatePosition();
    const onReflow = () => updatePosition();
    window.addEventListener("resize", onReflow);
    window.addEventListener("scroll", onReflow, true);
    return () => {
      window.removeEventListener("resize", onReflow);
      window.removeEventListener("scroll", onReflow, true);
    };
  }, [open, updatePosition]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      const t = e.target as Node;
      if (buttonRef.current?.contains(t) || menuRef.current?.contains(t)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!user) return null;

  const menuPanel = open ? (
    <div
      ref={menuRef}
      role="menu"
      className="rounded-xl border border-border bg-surface p-3 shadow-composer"
      style={{
        position: "fixed",
        left: menuPos.left,
        bottom: menuPos.bottom,
        width: MENU_WIDTH,
        zIndex: 9999,
      }}
    >
      <p className="text-[13px] font-medium text-text">{user.email}</p>
      <p className="text-[11px] text-text-faint">{roleLabel(role)}</p>
      <p className="mt-1 text-[11px] text-text-muted">{user.org_name}</p>

      <div className="my-3 flex items-center justify-between border-t border-border pt-3">
        <span className="text-[12px] text-text-muted">Theme</span>
        <ThemeToggleIcon />
      </div>

      <div className="space-y-0.5">
        <Link
          to="/settings"
          className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] text-text-muted hover:bg-surface-hover hover:text-text"
          onClick={() => setOpen(false)}
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
        {isAdminRole(role) && (
          <Link
            to="/admin"
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] text-text-muted hover:bg-surface-hover hover:text-text"
            onClick={() => setOpen(false)}
          >
            <Shield className="h-4 w-4" />
            Admin panel
          </Link>
        )}
        <button
          type="button"
          className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] text-text-muted hover:bg-surface-hover hover:text-text"
          onClick={() => {
            setOpen(false);
            void logout();
          }}
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </div>
  ) : null;

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => {
          setOpen((v) => {
            const next = !v;
            if (next) updatePosition();
            return next;
          });
        }}
        className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition ${
          open ? "bg-surface-raised" : "hover:bg-surface-hover"
        }`}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-orange-500/20 text-[11px] font-semibold text-orange-300">
          {initials(user.email)}
        </span>
        {!collapsed && (
          <>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[13px] font-medium text-text">
                {user.email.split("@")[0]}
              </span>
              <span className="block truncate text-[11px] text-text-faint">{user.org_name}</span>
            </span>
            <ChevronRight
              className={`h-4 w-4 shrink-0 text-text-faint transition ${open ? "rotate-90" : ""}`}
              aria-hidden
            />
          </>
        )}
      </button>
      {menuPanel ? createPortal(menuPanel, document.body) : null}
    </>
  );
}
