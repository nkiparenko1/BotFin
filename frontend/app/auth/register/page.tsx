"use client";

import Link from "next/link";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!consent) {
      setError("Необходимо согласие на обработку персональных данных");
      return;
    }
    setError("");
    const res = await signIn("credentials", {
      email,
      password,
      name,
      mode: "register",
      redirect: false,
    });
    if (res?.error) {
      setError("Не удалось зарегистрироваться. Возможно, email уже занят.");
      return;
    }
    router.push("/onboarding");
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white p-8 rounded-xl border shadow-sm">
        <h1 className="text-2xl font-bold mb-6">Регистрация</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Имя"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border rounded-lg px-4 py-2"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border rounded-lg px-4 py-2"
            required
          />
          <input
            type="password"
            placeholder="Пароль (мин. 6 символов)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border rounded-lg px-4 py-2"
            minLength={6}
            required
          />
          <label className="flex items-start gap-2 text-sm text-slate-600">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
            <span>
              Согласен на обработку персональных данных согласно{" "}
              <Link href="/privacy" className="text-primary">
                политике конфиденциальности
              </Link>
            </span>
          </label>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit" className="w-full bg-primary text-white py-2 rounded-lg hover:bg-blue-700">
            Начать бесплатно
          </button>
        </form>
        <p className="mt-4 text-sm text-center text-slate-500">
          Уже есть аккаунт?{" "}
          <Link href="/auth/login" className="text-primary">
            Войти
          </Link>
        </p>
      </div>
    </div>
  );
}
