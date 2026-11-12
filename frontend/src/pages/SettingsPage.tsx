import { ThemeToggle } from "../components/ThemeToggle";
import { Card } from "../components/ui/Card";

export function SettingsPage() {
  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h1 className="text-[22px] font-semibold tracking-tight text-text">Settings</h1>
      <Card className="flex items-center justify-between p-4">
        <div>
          <p className="text-[13px] font-medium text-text">Appearance</p>
          <p className="text-[12px] text-text-faint">System, dark, or light — Lucius-style tokens.</p>
        </div>
        <ThemeToggle />
      </Card>
    </div>
  );
}
