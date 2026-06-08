"use client";

import { signOut, useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { HealthScoreCard } from "@/components/HealthScoreCard";
import { apiFetch } from "@/lib/api-client";
import { useRouter } from "next/navigation";

export default function ProfilePage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [score, setScore] = useState(0);
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (!session?.accessToken) return;
    apiFetch<{ profile: { health_score?: number }; health_score?: number }>("/api/profile", {
      token: session.accessToken,
    }).then((res) => setScore(res.health_score || res.profile?.health_score || 0));
    apiFetch<{ user: { email: string } }>("/api/auth/me", { token: session.accessToken }).then((res) => {
      setEmail(res.user.email);
    });
  }, [session]);

  async function deleteAccount() {
    if (!session?.accessToken || !confirm("Удалить аккаунт и все данные?")) return;
    await apiFetch("/api/auth/me", { method: "DELETE", token: session.accessToken });
    signOut({ callbackUrl: "/" });
  }

  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-6">Профиль</h1>
      <div className="bg-white p-6 rounded-xl border max-w-md space-y-4">
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Тариф:</strong> Free</p>
        <HealthScoreCard score={score} size="sm" />
        <button
          onClick={() => router.push("/onboarding")}
          className="w-full border border-primary text-primary py-2 rounded-lg"
        >
          Пройти онбординг заново
        </button>
        <button onClick={deleteAccount} className="w-full border border-red-500 text-red-500 py-2 rounded-lg">
          Удалить аккаунт
        </button>
      </div>
    </AppShell>
  );
}
