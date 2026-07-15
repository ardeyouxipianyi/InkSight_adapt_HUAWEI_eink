import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const url = req.nextUrl.searchParams.get("url");
  if (!url) {
    return NextResponse.json({ error: "Missing url param" }, { status: 400 });
  }

  try {
    const parsed = new URL(url);
    const isGithub =
      parsed.hostname === "github.com" ||
      parsed.hostname.endsWith(".githubusercontent.com");
    if (!isGithub) {
      return NextResponse.json(
        { error: "Only GitHub URLs are allowed" },
        { status: 403 },
      );
    }
  } catch {
    return NextResponse.json({ error: "Invalid URL" }, { status: 400 });
  }

  try {
    const upstream = await fetch(url, { redirect: "follow", cache: "no-store" });
    if (!upstream.ok) {
      return new NextResponse(`Upstream returned ${upstream.status}`, {
        status: upstream.status,
      });
    }

    const body = upstream.body;
    if (!body) {
      return NextResponse.json({ error: "Empty response" }, { status: 502 });
    }

    const contentLength = upstream.headers.get("content-length");
    const headers: Record<string, string> = {
      "content-type": "application/octet-stream",
      "cache-control": "no-store",
    };
    if (contentLength) {
      headers["content-length"] = contentLength;
    }

    return new NextResponse(body, { status: 200, headers });
  } catch (error) {
    const msg = error instanceof Error ? error.message : "Download failed";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
