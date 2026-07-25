import { NextRequest, NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  const auth = request.headers.get("authorization");
  const expected = process.env.ADMIN_PASSWORD;

  if (!expected) {
    // Fail closed: if no password is configured, block admin access entirely
    // rather than leaving it open.
    return new NextResponse("Admin password not configured.", { status: 503 });
  }

  if (auth) {
    const [scheme, encoded] = auth.split(" ");
    if (scheme === "Basic" && encoded) {
      const decoded = Buffer.from(encoded, "base64").toString("utf-8");
      const [, password] = decoded.split(":");
      if (password === expected) {
        return NextResponse.next();
      }
    }
  }

  return new NextResponse("Authentication required.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="chirumaru admin"' },
  });
}

export const config = {
  matcher: ["/admin/:path*"],
};
