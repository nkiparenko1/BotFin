"use client";

import { useSession } from "next-auth/react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { AppShell } from "@/components/AppShell";
import { apiFetch, apiStream } from "@/lib/api-client";

interface Deduction {
  type: string;
  title: string;
  amount: number;
  article: string;
}

export default function TaxPage() {
  const { data: session } = useSession();
  const [form, setForm] = useState<Record<string, unknown>>({ employment_type: "employee" });
  const [deductions, setDeductions] = useState<Deduction[]>([]);
  const [total, setTotal] = useState(0);
  const [calcId, setCalcId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  function update(key: string, value: unknown) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function saveProfile() {
    if (!session?.accessToken) return;
    await apiFetch("/api/tax/profile", {
      method: "POST",
      token: session.accessToken,
      body: JSON.stringify(form),
    });
  }

  async function calculate() {
    if (!session?.accessToken) return;
    await saveProfile();
    const res = await apiFetch<{
      calculation_id: string;
      deductions: Deduction[];
      total_return: number;
    }>("/api/tax/calculate", { method: "POST", token: session.accessToken });
    setDeductions(res.deductions);
    setTotal(res.total_return);
    setCalcId(res.calculation_id);
  }

  async function askAi() {
    if (!session?.accessToken || !question.trim()) return;
    setAnswer("");
    let text = "";
    await apiStream(
      "/api/tax/ask",
      { question, calculation_id: calcId },
      session.accessToken,
      (chunk) => {
        text += chunk;
        setAnswer(text);
      },
    );
  }

  return (
    <AppShell>
      <h1 className="text-2xl font-bold mb-6">Налоговый советник</h1>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border space-y-3">
          <h2 className="font-semibold">Анкета</h2>
          <select className="w-full border rounded-lg px-3 py-2" onChange={(e) => update("employment_type", e.target.value)}>
            <option value="employee">Наёмный сотрудник</option>
            <option value="self_employed">Самозанятый</option>
            <option value="entrepreneur">ИП</option>
          </select>
          <label className="flex items-center gap-2">
            <input type="checkbox" onChange={(e) => update("bought_property", e.target.checked)} />
            Покупка квартиры за 3 года
          </label>
          <input type="number" placeholder="Сумма покупки" className="w-full border rounded-lg px-3 py-2" onChange={(e) => update("property_amount", +e.target.value)} />
          <label className="flex items-center gap-2">
            <input type="checkbox" onChange={(e) => update("has_mortgage", e.target.checked)} />
            Ипотека
          </label>
          <input type="number" placeholder="Уплаченные проценты" className="w-full border rounded-lg px-3 py-2" onChange={(e) => update("mortgage_interest_paid", +e.target.value)} />
          <label className="flex items-center gap-2">
            <input type="checkbox" onChange={(e) => update("paid_education", e.target.checked)} />
            Платное обучение
          </label>
          <input type="number" placeholder="Сумма обучения" className="w-full border rounded-lg px-3 py-2" onChange={(e) => update("education_amount", +e.target.value)} />
          <label className="flex items-center gap-2">
            <input type="checkbox" onChange={(e) => update("paid_medical", e.target.checked)} />
            Лечение / лекарства
          </label>
          <input type="number" placeholder="Сумма лечения" className="w-full border rounded-lg px-3 py-2" onChange={(e) => update("medical_amount", +e.target.value)} />
          <label className="flex items-center gap-2">
            <input type="checkbox" onChange={(e) => update("has_iis", e.target.checked)} />
            ИИС
          </label>
          <input type="number" placeholder="Взносы на ИИС" className="w-full border rounded-lg px-3 py-2" onChange={(e) => update("iis_amount", +e.target.value)} />
          <button onClick={calculate} className="w-full bg-primary text-white py-2 rounded-lg">
            Рассчитать вычеты
          </button>
        </div>

        <div className="space-y-4">
          {deductions.length > 0 && (
            <div className="bg-white p-6 rounded-xl border">
              <h2 className="font-semibold mb-4">Доступные вычеты</h2>
              <p className="text-2xl font-bold text-primary mb-4">Итого: {total.toLocaleString("ru-RU")} ₽</p>
              {deductions.map((d) => (
                <div key={d.type} className="border-t py-3">
                  <p className="font-medium">{d.title}</p>
                  <p className="text-sm text-slate-600">{d.article}</p>
                  <p className="text-primary">{d.amount.toLocaleString("ru-RU")} ₽</p>
                </div>
              ))}
            </div>
          )}

          {calcId && (
            <div className="bg-white p-6 rounded-xl border">
              <h2 className="font-semibold mb-2">Спросить AI</h2>
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Объясни мои вычеты..."
                className="w-full border rounded-lg px-3 py-2 mb-2"
              />
              <button onClick={askAi} className="w-full border border-primary text-primary py-2 rounded-lg mb-4">
                Спросить
              </button>
              {answer && <div className="prose prose-sm"><ReactMarkdown>{answer}</ReactMarkdown></div>}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
