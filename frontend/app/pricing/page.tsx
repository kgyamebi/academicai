import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

const plans = [
  ["Free", "$0", "2 checks / month · 2,000 words", "Basic grammar, structure, question analysis, basic academic feedback"],
  ["Student", "$1.99", "20 checks / month · 10,000 words", "Full analysis, thesis, argument, evidence, citation and reference checking"],
  ["Pro Student", "$3.99", "60 checks / month · larger documents", "Rubric, version comparison, Coach, AI-writing indicators, PDF reports, history"],
  ["Power", "$7.99", "200 checks / month · large documents", "Multiple projects, priority processing, extended history"],
];

export default function PricingPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-4 py-16">
        <h1 className="font-serif text-4xl">Affordable plans for students</h1>
        <p className="mt-3 max-w-2xl text-[var(--ink)]/70">Prices are configurable in the admin panel. Displayed local currency is for guidance; charging uses the payment provider that can serve your country.</p>
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {plans.map(([name, price, limit, features]) => (
            <article key={name} className="rounded-xl border border-[var(--rule)] bg-[var(--paper-2)] p-6">
              <h2 className="font-serif text-2xl">{name}</h2>
              <p className="mt-2 text-3xl">{price}<span className="text-base">/month</span></p>
              <p className="mt-2 text-sm">{limit}</p>
              <p className="mt-4 text-sm leading-6">{features}</p>
            </article>
          ))}
        </div>
        <p className="mt-8 text-sm">Institution plans are custom: multiple users, admin analytics, branding, SSO and central billing.</p>
      </main>
      <SiteFooter />
    </>
  );
}
