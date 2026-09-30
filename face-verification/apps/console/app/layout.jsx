import "./globals.css";
import AppProvider from "@/components/AppProvider";
import AppShell from "@/components/AppShell";

export const metadata = {
  title: { default: "FaceGate — Identity Verification Console", template: "%s — FaceGate" },
  description: "Operator console for 1:1 face verification, 1:N identification and enrollment.",
  robots: { index: false, follow: false },
};

export const viewport = { width: "device-width", initialScale: 1 };

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <AppProvider>
          <AppShell>{children}</AppShell>
        </AppProvider>
      </body>
    </html>
  );
}
