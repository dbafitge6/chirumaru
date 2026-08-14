import Link from 'next/link';
import { Metadata } from 'next';
import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import matter from 'gray-matter';
import ReactMarkdown from 'react-markdown';

interface ArticlePageProps {
  params: Promise<{
    slug: string;
  }>;
}

interface ArticleData {
  title: string;
  description: string;
  date: string;
  slug: string;
}

async function getArticle(slug: string) {
  const articlesDir = join(process.cwd(), 'content', 'articles');
  const filePath = join(articlesDir, `${slug}.md`);

  try {
    const content = await readFile(filePath, 'utf-8');
    const { data, content: body } = matter(content);

    return {
      data: data as ArticleData,
      body,
    };
  } catch {
    return null;
  }
}

async function getAllSlugs() {
  const articlesDir = join(process.cwd(), 'content', 'articles');
  const files = await readdir(articlesDir);

  return files
    .filter((file) => file.endsWith('.md'))
    .map((file) => file.replace('.md', ''));
}

export async function generateStaticParams() {
  const slugs = await getAllSlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: ArticlePageProps): Promise<Metadata> {
  const resolvedParams = await params;
  const article = await getArticle(resolvedParams.slug);

  if (!article) {
    return {
      title: 'Not Found',
    };
  }

  return {
    title: `${article.data.title} | ちるまる`,
    description: article.data.description,
    openGraph: {
      title: `${article.data.title} | ちるまる`,
      description: article.data.description,
      type: 'article',
      publishedTime: article.data.date,
      locale: 'ja_JP',
    },
  };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const resolvedParams = await params;
  const article = await getArticle(resolvedParams.slug);

  if (!article) {
    return (
      <main className="min-h-screen bg-white px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">記事が見つかりません</h1>
          <Link href="/articles" className="text-blue-600 hover:underline">
            記事一覧に戻る
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <Link href="/articles" className="text-blue-600 hover:underline mb-8 inline-block">
          ← 記事一覧に戻る
        </Link>

        <article className="prose prose-sm max-w-none">
          <header className="mb-8 border-b border-gray-200 pb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              {article.data.title}
            </h1>
            <time className="text-gray-500">
              {new Date(article.data.date).toLocaleDateString('ja-JP')}
            </time>
          </header>

          <div className="prose prose-sm max-w-none prose-headings:font-bold prose-headings:text-gray-900 prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline">
            <ReactMarkdown>{article.body}</ReactMarkdown>
          </div>
        </article>

        <footer className="mt-12 border-t border-gray-200 pt-8">
          <Link href="/articles" className="text-blue-600 hover:underline">
            記事一覧に戻る
          </Link>
        </footer>
      </div>
    </main>
  );
}
