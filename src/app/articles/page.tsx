import Link from 'next/link';
import { Metadata } from 'next';
import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import matter from 'gray-matter';

export const metadata: Metadata = {
  title: '読みもの | ちるまる',
  description: 'ちるまるについての記事や情報をお読みください。',
  openGraph: {
    title: '読みもの | ちるまる',
    description: 'ちるまるについての記事や情報をお読みください。',
    type: 'website',
    locale: 'ja_JP',
  },
};

interface Article {
  slug: string;
  title: string;
  description: string;
  date: string;
}

async function getArticles(): Promise<Article[]> {
  const articlesDir = join(process.cwd(), 'content', 'articles');
  const files = await readdir(articlesDir);

  const articles: Article[] = [];

  for (const file of files) {
    if (!file.endsWith('.md')) continue;

    const filePath = join(articlesDir, file);
    const content = await readFile(filePath, 'utf-8');
    const { data } = matter(content);

    articles.push({
      slug: data.slug,
      title: data.title,
      description: data.description,
      date: data.date,
    });
  }

  return articles.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

export default async function ArticlesPage() {
  const articles = await getArticles();

  return (
    <main className="min-h-screen bg-white px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-3xl font-bold text-gray-900">読みもの</h1>

        {articles.length === 0 ? (
          <p className="text-gray-500">記事がまだありません。</p>
        ) : (
          <div className="space-y-6">
            {articles.map((article) => (
              <article key={article.slug} className="border-b border-gray-200 pb-6 last:border-b-0">
                <Link
                  href={`/articles/${article.slug}`}
                  className="hover:opacity-80 transition-opacity"
                >
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    {article.title}
                  </h2>
                  <p className="text-gray-600 mb-3">
                    {article.description}
                  </p>
                  <time className="text-sm text-gray-500">
                    {new Date(article.date).toLocaleDateString('ja-JP')}
                  </time>
                </Link>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
