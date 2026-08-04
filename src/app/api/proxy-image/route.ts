export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const url = searchParams.get('url');

  if (!url) {
    return new Response('Missing url parameter', { status: 400 });
  }

  try {
    // Handle Google Drive URLs
    let imageUrl = url;
    if (url.includes('drive.google.com/open?id=')) {
      const id = url.match(/id=([^&]+)/)?.[1];
      if (id) {
        imageUrl = `https://drive.google.com/uc?id=${id}&export=view`;
      }
    }

    const response = await fetch(imageUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      },
    });

    if (!response.ok) {
      return new Response('Failed to fetch image', { status: 404 });
    }

    const contentType = response.headers.get('content-type') || 'image/jpeg';
    const buffer = await response.arrayBuffer();

    return new Response(buffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (error) {
    console.error('Image proxy error:', error);
    return new Response('Internal server error', { status: 500 });
  }
}
