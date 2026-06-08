import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";

/** Skip unresolved Railway refs and malformed bases (e.g. http://:8000 when service name is wrong). */
function isValidBackendBase(url: string | undefined): url is string {
  if (!url || url.includes("${{")) return false;
  try {
    return Boolean(new URL(url).hostname);
  } catch {
    return false;
  }
}

/** Server-side URL (NextAuth runs in Node). Prefer private Railway network, then public API. */
function getBackendBaseUrls(): string[] {
  const urls = [process.env.INTERNAL_API_URL, process.env.NEXT_PUBLIC_API_URL].filter(isValidBackendBase);
  return Array.from(new Set(urls));
}

async function backendFetch(path: string, init?: RequestInit): Promise<Response | null> {
  let lastError: unknown;
  for (const base of getBackendBaseUrls()) {
    try {
      const res = await fetch(`${base.replace(/\/$/, "")}${path}`, init);
      if (res.ok) return res;
      console.error(`Backend ${base}${path} -> ${res.status}`);
    } catch (err) {
      lastError = err;
      console.error(`Backend ${base}${path} failed:`, err);
    }
  }
  if (lastError) console.error("All backend URLs failed for", path, lastError);
  return null;
}

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    refreshToken?: string;
    user: { id?: string; name?: string | null; email?: string | null; image?: string | null };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    userId?: string;
  }
}

async function refreshAccessToken(refreshToken: string) {
  const res = await backendFetch("/api/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res) throw new Error("Refresh failed");
  const data = await res.json();
  return data.access_token as string;
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        mode: { label: "Mode", type: "text" },
        name: { label: "Name", type: "text" },
      },
      async authorize(credentials) {
        if (credentials?.mode === "guest") {
          const res = await backendFetch("/api/auth/guest", { method: "POST" });
          if (!res) return null;
          const data = await res.json();
          return {
            id: data.user.id,
            email: data.user.email,
            name: data.user.name,
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
          } as never;
        }
        if (!credentials?.email || !credentials?.password) return null;
        const isRegister = credentials.mode === "register";
        const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
        const body = isRegister
          ? { email: credentials.email, password: credentials.password, name: credentials.name || "User" }
          : { email: credentials.email, password: credentials.password };

        const res = await backendFetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res) return null;
        const data = await res.json();
        return {
          id: data.user.id,
          email: data.user.email,
          name: data.user.name,
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
        } as never;
      },
    }),
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        const u = user as { accessToken?: string; refreshToken?: string; id?: string };
        token.accessToken = u.accessToken;
        token.refreshToken = u.refreshToken;
        token.userId = u.id;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.refreshToken = token.refreshToken as string;
      if (session.user) session.user.id = token.userId as string;
      return session;
    },
  },
  pages: {
    signIn: "/auth/login",
  },
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET,
};
