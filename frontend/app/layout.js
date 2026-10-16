import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata = {
  title: "PromoMind AI — Intelligent Demand Forecasting & Profit Optimization for Retail & Commerce",
  description: "AI-Powered Demand Forecasting, Dynamic Sales Copilot & Capital Profit Optimization for Retail & Commerce",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased light">
      <body className="min-h-full flex flex-col bg-background text-foreground font-sans selection:bg-primary/10 selection:text-primary">
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
