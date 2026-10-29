import { AuthGuard } from "@/components/auth/auth-guard";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { TopNavbar } from "@/components/dashboard/top-navbar";
import { DemoBanner } from "@/components/dashboard/demo-banner";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopNavbar />
          <main id="main-content" tabIndex={-1} className="min-w-0 flex-1 p-4 pb-12 sm:p-8 lg:p-10"><div className="mx-auto w-full max-w-7xl"><DemoBanner />{children}</div></main>
        </div>
      </div>
    </AuthGuard>
  );
}
