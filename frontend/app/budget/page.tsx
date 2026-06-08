"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { apiFetch, apiStream } from "@/lib/api-client";
import ReactMarkdown from "react-markdown";

interface Transaction {
  id: string;
  amount: number;
  category: string;
  description?: string;
  date: string;
}

const CATEGORIES = ["food", "transport", "housing", "subscriptions", "entertainment", "health", "other"];

export default function BudgetPage() {
  const { data: session } = useSession();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("food");
  const [description, setDescription] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  const month = new Date().toISOString().slice(0, 7);

  function load() {
    if (!session?.accessToken) return;
    apiFetch<Transaction[]>(`/api/budget/transactions?month=${month}`, {
      token: session.accessToken,
    }).then(setTransactions);
  }

  useEffect(load, [session, month]);

  async function addTransaction(e: React.FormEvent) {
    e.preventDefault();
    if (!session?.accessToken) return;
    await apiFetch("/api/budget/transactions", {
      method: "POST",
      token: session.accessToken,
      body: JSON.stringify({
        amount: +amount,
        category,
        date: new Date().toISOString().slice(0, 10),
        description,
      }),
    });
    setAmount("");
    setDescription("");
    load();
  }

  async function analyze() {
    if (!session?.accessToken) return;
    setAnalyzing(true);
    setAnalysis("");
    let text = "";
    try {
      await apiStream("/api/budget/analyze", { month }, session.accessToken, (chunk) => {
        text += chunk;
        setAnalysis(text);
      });
    } finally {
      setAnalyzing(false);
    }
  }

  async function importCsv(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !session?.accessToken) return;
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/budget/import-csv`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session.accessToken}` },
      body: form,
    });
    const data = await res.json();
    if (data.preview?.length) {
      await apiFetch("/api/budget/import-csv/confirm", {
        method: "POST",
        token: session.accessToken,
        body: JSON.stringify({ transactions: data.preview }),
      });
      load();
    }
  }

  const byCategory: Record<string, number> = {};
  transactions.forEach((t) => {
    byCategory[t.category] = (byCategory[t.category] || 0) + Number(t.amount);
  });

  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-6">Бюджет</h1>

      <div className="grid md:grid-cols-2 gap-6">
        <form onSubmit={addTransaction} className="bg-white p-6 rounded-xl border space-y-3">
          <h2 className="font-semibold">Добавить расход</h2>
          <input type="number" placeholder="Сумма" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full border rounded-lg px-3 py-2" required />
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full border rounded-lg px-3 py-2">
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <input placeholder="Комментарий" value={description} onChange={(e) => setDescription(e.target.value)} className="w-full border rounded-lg px-3 py-2" />
          <button type="submit" className="w-full bg-primary text-white py-2 rounded-lg">Добавить</button>
          <label className="block text-sm text-primary cursor-pointer">
            Импорт CSV
            <input type="file" accept=".csv" className="hidden" onChange={importCsv} />
          </label>
        </form>

        <div className="bg-white p-6 rounded-xl border">
          <h2 className="font-semibold mb-4">По категориям ({month})</h2>
          {Object.entries(byCategory).map(([cat, sum]) => (
            <div key={cat} className="flex justify-between py-2 border-b text-sm">
              <span>{cat}</span>
              <span>{sum.toLocaleString("ru-RU")} ₽</span>
            </div>
          ))}
          <button onClick={analyze} disabled={analyzing} className="mt-4 w-full border border-primary text-primary py-2 rounded-lg">
            {analyzing ? "Анализ..." : "Проанализировать"}
          </button>
        </div>
      </div>

      {analysis && (
        <div className="mt-6 bg-white p-6 rounded-xl border prose prose-sm max-w-none">
          <h2 className="font-semibold mb-2">AI-анализ</h2>
          <ReactMarkdown>{analysis}</ReactMarkdown>
        </div>
      )}

      <div className="mt-6 bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="text-left p-3">Дата</th>
              <th className="text-left p-3">Категория</th>
              <th className="text-right p-3">Сумма</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr key={t.id} className="border-t">
                <td className="p-3">{t.date}</td>
                <td className="p-3">{t.category}</td>
                <td className="p-3 text-right">{Number(t.amount).toLocaleString("ru-RU")} ₽</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
