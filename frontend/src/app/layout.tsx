import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bird Diversity Ranking",
  description: "Compare bird species diversity across towns and villages using eBird data",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
        <Navbar />
        <main style={{ flex: 1, maxWidth: 960, width: "100%", margin: "0 auto", padding: "1.5rem 1.25rem" }}>
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
