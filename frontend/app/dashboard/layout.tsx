import { AuthGuard } from "@/components/auth/auth-guard";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { TopNavbar } from "@/components/dashboard/top-navbar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopNavbar />
          <main className="flex-1 bg-muted/40 p-4 sm:p-6">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}
