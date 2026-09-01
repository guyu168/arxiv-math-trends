'use client';

import { type FormEvent, useEffect, useMemo, useState } from 'react';
import { BarChart3, CalendarRange, Database, Sigma, Users } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

type Snapshot = {
  min_date: string;
  max_date: string;
  generated_at: string;
  paper_count: number;
  authors: string[];
  paper_days: Record<string, number>;
  days: Record<string, [number, number][]>;
};

type Ranking = { name: string; count: number };
type Result = { ranking: Ranking[]; papers: number; activeAuthors: number; days: number };

const DAY_MS = 86_400_000;

function daySpan(start: string, end: string) {
  return Math.round((Date.parse(`${end}T00:00:00Z`) - Date.parse(`${start}T00:00:00Z`)) / DAY_MS);
}

function calculate(snapshot: Snapshot, start: string, end: string): Result {
  const counts = new Uint32Array(snapshot.authors.length);
  let papers = 0;
  for (const [day, value] of Object.entries(snapshot.paper_days)) {
    if (day >= start && day <= end) papers += value;
  }
  for (const [day, entries] of Object.entries(snapshot.days)) {
    if (day < start || day > end) continue;
    for (const [authorId, count] of entries) counts[authorId] += count;
  }
  const ranking: Ranking[] = [];
  counts.forEach((count, authorId) => {
    if (count) ranking.push({ name: snapshot.authors[authorId], count });
  });
  ranking.sort((left, right) => right.count - left.count || left.name.localeCompare(right.name));
  return {
    ranking: ranking.slice(0, 50),
    papers,
    activeAuthors: ranking.length,
    days: daySpan(start, end) + 1,
  };
}

export default function Home() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [start, setStart] = useState('2026-01-01');
  const [end, setEnd] = useState('2026-06-30');
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/data/author_daily.json')
      .then((response) => {
        if (!response.ok) throw new Error('Snapshot could not be loaded.');
        return response.json() as Promise<Snapshot>;
      })
      .then((data) => {
        const initialStart = data.min_date <= '2026-01-01' ? '2026-01-01' : data.min_date;
        setSnapshot(data);
        setStart(initialStart);
        setEnd(data.max_date);
        setResult(calculate(data, initialStart, data.max_date));
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const maximum = result?.ranking[0]?.count ?? 1;
  const generated = useMemo(
    () => snapshot && new Date(snapshot.generated_at).toLocaleDateString('en-CA'),
    [snapshot],
  );

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!snapshot) return;
    if (!start || !end || start > end) {
      setError('Choose a valid start and end date.');
      return;
    }
    if (start < snapshot.min_date || end > snapshot.max_date) {
      setError(`Dates must stay within ${snapshot.min_date} and ${snapshot.max_date}.`);
      return;
    }
    if (daySpan(start, end) <= 15) {
      setError('The selected period must be longer than 15 days.');
      return;
    }
    setError('');
    setResult(calculate(snapshot, start, end));
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/80 bg-card/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground"><Sigma className="size-5" /></span>
            <div><p className="font-heading text-base font-semibold tracking-tight">arXiv Math Observatory</p><p className="text-xs text-muted-foreground">Author activity · 2024–2026 snapshot</p></div>
          </div>
          <Badge variant="outline" className="hidden sm:inline-flex">Primary math categories</Badge>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-6 px-5 py-7 sm:px-8 lg:grid-cols-[340px_minmax(0,1fr)]">
        <section className="space-y-5">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-primary">Explore a window</p>
            <h1 className="font-heading text-3xl font-semibold leading-tight tracking-tight">Who is publishing most in mathematics?</h1>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">Choose a period longer than 15 days. Each paper adds one count to every listed author.</p>
          </div>

          <Card className="shadow-sm">
            <CardHeader><CardTitle className="flex items-center gap-2"><CalendarRange className="size-4 text-primary" />Date range</CardTitle><CardDescription>{snapshot ? `Available: ${snapshot.min_date} to ${snapshot.max_date}` : 'Loading snapshot bounds…'}</CardDescription></CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submit}>
                <label className="grid gap-1.5 text-xs font-medium">Start date<Input aria-label="Start date" type="date" value={start} min={snapshot?.min_date} max={snapshot?.max_date} onChange={(event) => setStart(event.target.value)} className="h-10" /></label>
                <label className="grid gap-1.5 text-xs font-medium">End date<Input aria-label="End date" type="date" value={end} min={snapshot?.min_date} max={snapshot?.max_date} onChange={(event) => setEnd(event.target.value)} className="h-10" /></label>
                {error && <p role="alert" className="rounded-md border border-destructive/25 bg-destructive/8 px-3 py-2 text-xs leading-5 text-destructive">{error}</p>}
                <Button type="submit" size="lg" className="w-full" disabled={!snapshot}><BarChart3 />Rank top 50</Button>
              </form>
              <p className="mt-4 text-xs leading-5 text-muted-foreground">Author names follow arXiv metadata exactly; spelling variants are not merged.</p>
            </CardContent>
          </Card>

          {snapshot && <div className="grid grid-cols-2 gap-3 text-xs"><div className="rounded-lg border bg-card p-3"><Database className="mb-2 size-4 text-primary" /><span className="block font-mono text-base font-semibold">{snapshot.paper_count.toLocaleString()}</span><span className="text-muted-foreground">papers in snapshot</span></div><div className="rounded-lg border bg-card p-3"><Users className="mb-2 size-4 text-primary" /><span className="block font-mono text-base font-semibold">{snapshot.authors.length.toLocaleString()}</span><span className="text-muted-foreground">author-name records</span></div></div>}
        </section>

        <Card className="min-w-0 shadow-sm">
          <CardHeader className="border-b">
            <CardTitle className="text-xl">Top mathematics authors</CardTitle>
            <CardDescription>{result ? `${start} → ${end} · ${result.days} days · ${result.papers.toLocaleString()} papers · ${result.activeAuthors.toLocaleString()} active author names` : 'Preparing the ranking…'}</CardDescription>
          </CardHeader>
          <CardContent>
            {!result ? <div className="space-y-3 py-3">{Array.from({ length: 10 }, (_, index) => <Skeleton key={index} className="h-9 w-full" />)}</div> : (
              <Table>
                <TableHeader><TableRow><TableHead className="w-16">Rank</TableHead><TableHead>Author</TableHead><TableHead className="hidden w-40 sm:table-cell">Relative activity</TableHead><TableHead className="text-right">Papers</TableHead></TableRow></TableHeader>
                <TableBody>{result.ranking.map((author, index) => <TableRow key={`${author.name}-${index}`}><TableCell className="font-mono text-muted-foreground">{String(index + 1).padStart(2, '0')}</TableCell><TableCell className="max-w-[18rem] truncate font-medium" title={author.name}>{author.name}</TableCell><TableCell className="hidden sm:table-cell"><span className="block h-1.5 overflow-hidden rounded-full bg-muted"><span className="block h-full rounded-full bg-primary/75" style={{ width: `${Math.max(4, (author.count / maximum) * 100)}%` }} /></span></TableCell><TableCell className="text-right font-mono font-semibold">{author.count}</TableCell></TableRow>)}</TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      <footer className="border-t px-5 py-5 text-center text-xs text-muted-foreground">Frozen from the official arXiv API · primary mathematics categories · snapshot generated {generated || '—'}</footer>
    </main>
  );
}
