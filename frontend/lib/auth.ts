import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";

/** Server-side URL (NextAuth runs in Node). In Docker use http://backend:8000. */
const SERVER_API_URL =
  process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const res = await fetch(`${SERVER_API_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) throw new Error("Refresh failed");
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
          const res = await fetch(`${SERVER_API_URL}/api/auth/guest`, { method: "POST" });
          if (!res.ok) return null;
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

        const res = await fetch(`${SERVER_API_URL}${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok) return null;
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
