"use client";

interface ChapterContent {
  title: string;
  content: string;
  index: number;
}

interface ChapterReaderProps {
  content: ChapterContent | null;
  loading: boolean;
}

export default function ChapterReader({ content, loading }: ChapterReaderProps) {
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-3/4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-700 rounded w-5/6"></div>
            <div className="h-4 bg-gray-700 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center">
        <p className="text-gray-400">Chapter not found</p>
      </div>
    );
  }

  // Split content into paragraphs for better readability
  const paragraphs = content.content
    .split('\n')
    .map(p => p.trim())
    .filter(p => p.length > 0);

  return (
    <div className="max-w-4xl mx-auto p-8">
      <article className="prose prose-invert prose-lg max-w-none">
        <h1 className="text-3xl font-bold mb-8 text-center text-gray-100">
          {content.title}
        </h1>
        
        <div className="space-y-6 leading-relaxed">
          {paragraphs.map((paragraph, index) => (
            <p 
              key={index}
              className="text-gray-200 text-lg leading-8"
            >
              {paragraph}
            </p>
          ))}
        </div>
      </article>
    </div>
  );
}