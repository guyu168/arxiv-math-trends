'use client';

import { type ComponentProps, useEffect, useMemo, useState } from 'react';
import {
  BarChart3,
  Building2,
  CalendarRange,
  Database,
  Sigma,
  Users,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

type AuthorIdentity = { name: string; affiliation: string };
type Metadata = {
  min_date: string;
  max_date: string;
  generated_at: string;
  paper_count: number;
  author_identity_count: number;
  years: number[];
  identity_basis: string;
};
type YearSnapshot = {
  min_date: string;
  max_date: string;
  paper_count: number;
  authors: AuthorIdentity[];
  categories: string[];
  paper_days: Record<string, number>;
  days: Record<string, [number, number, number][]>;
};
type Ranking = AuthorIdentity & { count: number; categories: string[] };
type RankingAccumulator = AuthorIdentity & {
  count: number;
  categoryCounts: Map<string, number>;
};
type Result = {
  ranking: Ranking[];
  papers: number;
  activeAuthors: number;
  days: number;
};
type FormSubmitEvent = Parameters<
  NonNullable<ComponentProps<'form'>['onSubmit']>
>[0];

const DAY_MS = 86_400_000;
const yearCache = new Map<number, Promise<YearSnapshot>>();

function daySpan(start: string, end: string) {
  return Math.round(
    (Date.parse(`${end}T00:00:00Z`) - Date.parse(`${start}T00:00:00Z`)) /
      DAY_MS,
  );
}

function identityKey(author: AuthorIdentity) {
  return `${author.name}\\u0000${author.affiliation}`;
}

function formatCategory(category: string) {
  return category === 'math.AP' ? 'PDE' : category.replace(/^math\./, '');
}

function loadYear(year: number) {
  if (!yearCache.has(year)) {
    yearCache.set(
      year,
      fetch(`/data/authors/${year}.json`).then((response) => {
        if (!response.ok)
          throw new Error(`The ${year} snapshot could not be loaded.`);
        return response.json() as Promise<YearSnapshot>;
      }),
    );
  }
  return yearCache.get(year)!;
}

function calculate(
  snapshots: YearSnapshot[],
  start: string,
  end: string,
): Result {
  const counts = new Map<string, RankingAccumulator>();
  let papers = 0;
  for (const snapshot of snapshots) {
    for (const [day, value] of Object.entries(snapshot.paper_days)) {
      if (day >= start && day <= end) papers += value;
    }
    for (const [day, entries] of Object.entries(snapshot.days)) {
      if (day < start || day > end) continue;
      for (const [authorId, categoryId, count] of entries) {
        const author = snapshot.authors[authorId];
        const category = snapshot.categories[categoryId];
        const key = identityKey(author);
        const current = counts.get(key);
        if (current) {
          current.count += count;
          current.categoryCounts.set(
            category,
            (current.categoryCounts.get(category) ?? 0) + count,
          );
        } else {
          counts.set(key, {
            ...author,
            count,
            categoryCounts: new Map([[category, count]]),
          });
        }
      }
    }
  }
  const ranking = [...counts.values()]
    .map(({ categoryCounts, ...author }) => ({
      ...author,
      categories: [...categoryCounts.entries()]
        .sort(
          ([leftCategory, leftCount], [rightCategory, rightCount]) =>
            rightCount - leftCount || leftCategory.localeCompare(rightCategory),
        )
        .slice(0, 3)
        .map(([category]) => formatCategory(category)),
    }))
    .sort(
      (left, right) =>
        right.count - left.count ||
        left.name.localeCompare(right.name) ||
        left.affiliation.localeCompare(right.affiliation),
    );
  return {
    ranking: ranking.slice(0, 50),
    papers,
    activeAuthors: ranking.length,
    days: daySpan(start, end) + 1,
  };
}

async function calculateWindow(metadata: Metadata, start: string, end: string) {
  const startYear = Number(start.slice(0, 4));
  const endYear = Number(end.slice(0, 4));
  const years = metadata.years.filter(
    (year) => year >= startYear && year <= endYear,
  );
  return calculate(await Promise.all(years.map(loadYear)), start, end);
}

export default function Home() {
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [start, setStart] = useState('2026-01-01');
  const [end, setEnd] = useState('2026-08-31');
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/data/author_metadata.json')
      .then((response) => {
        if (!response.ok)
          throw new Error('Snapshot metadata could not be loaded.');
        return response.json() as Promise<Metadata>;
      })
      .then(async (data) => {
        const initialStart =
          data.min_date <= '2026-01-01' ? '2026-01-01' : data.min_date;
        setMetadata(data);
        setStart(initialStart);
        setEnd(data.max_date);
        setResult(await calculateWindow(data, initialStart, data.max_date));
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  const maximum = result?.ranking[0]?.count ?? 1;
  const generated = useMemo(
    () =>
      metadata && new Date(metadata.generated_at).toLocaleDateString('en-CA'),
    [metadata],
  );

  async function submit(event: FormSubmitEvent) {
    event.preventDefault();
    if (!metadata) return;
    if (!start || !end || start > end) {
      setError('Choose a valid start and end date.');
      return;
    }
    if (start < metadata.min_date || end > metadata.max_date) {
      setError(
        `Dates must stay within ${metadata.min_date} and ${metadata.max_date}.`,
      );
      return;
    }
    if (daySpan(start, end) <= 15) {
      setError('The selected period must be longer than 15 days.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      setResult(await calculateWindow(metadata, start, end));
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'The ranking could not be calculated.',
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/80 bg-card/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground">
              <Sigma className="size-5" />
            </span>
            <div>
              <p className="font-heading text-base font-semibold tracking-tight">
                arXiv Math Observatory
              </p>
              <p className="text-xs text-muted-foreground">
                Author activity · 2010–2026 snapshot
              </p>
            </div>
          </div>
          <Badge variant="outline" className="hidden sm:inline-flex">
            Name + affiliation identities
          </Badge>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-6 px-5 py-7 sm:px-8 lg:grid-cols-[340px_minmax(0,1fr)]">
        <section className="space-y-5">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
              Explore a window
            </p>
            <h1 className="font-heading text-3xl font-semibold leading-tight tracking-tight">
              Who is publishing most in mathematics?
            </h1>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              Choose a period longer than 15 days. Authors with the same name
              are separated when arXiv supplies different affiliations. Each row
              also shows that author&apos;s top three fields in the selected
              period.
            </p>
          </div>

          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalendarRange className="size-4 text-primary" />
                Date range
              </CardTitle>
              <CardDescription>
                {metadata
                  ? `Available: ${metadata.min_date} to ${metadata.max_date}`
                  : 'Loading snapshot bounds…'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submit}>
                <label
                  htmlFor="start-date"
                  className="grid gap-1.5 text-xs font-medium"
                >
                  Start date
                  <Input
                    aria-label="Start date"
                    id="start-date"
                    type="date"
                    value={start}
                    min={metadata?.min_date}
                    max={metadata?.max_date}
                    onChange={(event) => setStart(event.target.value)}
                    className="h-10"
                  />
                </label>
                <label
                  htmlFor="end-date"
                  className="grid gap-1.5 text-xs font-medium"
                >
                  End date
                  <Input
                    aria-label="End date"
                    id="end-date"
                    type="date"
                    value={end}
                    min={metadata?.min_date}
                    max={metadata?.max_date}
                    onChange={(event) => setEnd(event.target.value)}
                    className="h-10"
                  />
                </label>
                {error && (
                  <p
                    role="alert"
                    className="rounded-md border border-destructive/25 bg-destructive/8 px-3 py-2 text-xs leading-5 text-destructive"
                  >
                    {error}
                  </p>
                )}
                <Button
                  type="submit"
                  size="lg"
                  className="w-full"
                  disabled={!metadata || loading}
                >
                  <BarChart3 />
                  {loading ? 'Loading years…' : 'Rank top 50'}
                </Button>
              </form>
              <div className="mt-4 flex gap-2 text-xs leading-5 text-muted-foreground">
                <Building2 className="mt-0.5 size-4 shrink-0 text-primary" />
                <p>
                  arXiv&apos;s API does not expose author email addresses.
                  Affiliation is used instead; missing or changed affiliations
                  can still split or merge people.
                </p>
              </div>
            </CardContent>
          </Card>

          {metadata && (
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg border bg-card p-3">
                <Database className="mb-2 size-4 text-primary" />
                <span className="block font-mono text-base font-semibold">
                  {metadata.paper_count.toLocaleString()}
                </span>
                <span className="text-muted-foreground">
                  papers in snapshot
                </span>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <Users className="mb-2 size-4 text-primary" />
                <span className="block font-mono text-base font-semibold">
                  {metadata.author_identity_count.toLocaleString()}
                </span>
                <span className="text-muted-foreground">
                  name + affiliation records
                </span>
              </div>
            </div>
          )}
        </section>

        <Card className="min-w-0 shadow-sm">
          <CardHeader className="border-b">
            <CardTitle className="text-xl">Top mathematics authors</CardTitle>
            <CardDescription>
              {result
                ? `${start} → ${end} · ${result.days} days · ${result.papers.toLocaleString()} papers · ${result.activeAuthors.toLocaleString()} active identities`
                : 'Preparing the ranking…'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading || !result ? (
              <div className="space-y-3 py-3">
                {Array.from({ length: 10 }, (_, index) => (
                  <Skeleton key={index} className="h-12 w-full" />
                ))}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">Rank</TableHead>
                    <TableHead>Author · top fields · affiliation</TableHead>
                    <TableHead className="hidden w-40 sm:table-cell">
                      Relative activity
                    </TableHead>
                    <TableHead className="text-right">Papers</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.ranking.map((author, index) => (
                    <TableRow key={`${identityKey(author)}-${index}`}>
                      <TableCell className="font-mono text-muted-foreground">
                        {String(index + 1).padStart(2, '0')}
                      </TableCell>
                      <TableCell className="max-w-[22rem]">
                        <span
                          className="block truncate font-medium"
                          title={author.name}
                        >
                          {author.name}
                          <span className="ml-1.5 font-mono text-[0.7rem] font-semibold tracking-wide text-primary">
                            · {author.categories.join(' / ')}
                          </span>
                        </span>
                        <span
                          className="block truncate text-xs text-muted-foreground"
                          title={
                            author.affiliation || 'Affiliation not provided'
                          }
                        >
                          {author.affiliation || 'Affiliation not provided'}
                        </span>
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">
                        <span className="block h-1.5 overflow-hidden rounded-full bg-muted">
                          <span
                            className="block h-full rounded-full bg-primary/75"
                            style={{
                              width: `${Math.max(4, (author.count / maximum) * 100)}%`,
                            }}
                          />
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold">
                        {author.count}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      <footer className="border-t px-5 py-5 text-center text-xs text-muted-foreground">
        Frozen from the official arXiv API · primary mathematics categories ·
        snapshot generated {generated || '—'}
      </footer>
    </main>
  );
}
