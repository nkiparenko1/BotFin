import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const path = req.nextUrl.pathname;
    const isAuthPage = path.startsWith("/auth");
    const isPublic = path === "/" || path === "/privacy" || path === "/chat" || isAuthPage;

    if (!token && !isPublic) {
      return NextResponse.redirect(new URL("/auth/login", req.url));
    }
    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token, req }) => {
        const path = req.nextUrl.pathname;
        if (path === "/" || path === "/privacy" || path === "/chat" || path.startsWith("/auth")) return true;
        return !!token;
      },
    },
  },
);

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
