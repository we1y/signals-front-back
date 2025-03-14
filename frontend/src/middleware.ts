import { NextRequest, NextResponse } from "next/server";
import { api } from "@/api/instance.api";
import { CheckReferral } from "./types/referral.interface";
import { userService } from "./services/user.service";

// export const middleware = sslRedirect({
//     environments: ['development'],
//     status: 301,
// });

export async function middleware(request: NextRequest) {
    const { pathname, searchParams } = request.nextUrl;
    const referralMatch = pathname.match(/\/ref\/(\d+)-(\d+)/);
    // const expiresTime = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    const expiresTime = new Date(Date.now() + 60 * 60 * 1000);
    // const userAgent = request.headers.get('user-agent') || '';
    // const isMobile = /Mobi/i.test(userAgent);

    // const response = NextResponse.next();
    // response.cookies.set('isMobile', isMobile ? 'true' : 'false');


    if (pathname === '/auth' && searchParams.has('token')) {
        const authToken = searchParams.get('token');
        console.log(authToken);

        if (authToken) {
            const response = NextResponse.redirect(new URL('/', request.url));
            response.cookies.set('auth', authToken, { path: '/', expires: expiresTime });
            return response;
        } else {
            console.error('Token is null');
            return NextResponse.redirect(new URL('/error', request.url));
        }
    }


    if (referralMatch) {
        try {
            const user = await userService.getUser();
            if (!user || !user.telegram_id) {
                console.error('User data is missing or invalid:', user);
                return NextResponse.redirect(new URL('/error', request.url));
            }
            console.log('User data:', user);

            const requestBody = {
                telegram_id: user.telegram_id,
                referral_link: `https://app.com${referralMatch[0]}`,
            };
            console.log('Sending request to /check_referral with body:', requestBody);

            const ref = await api.post<CheckReferral>('check_referral', requestBody);
            console.log('Response from /check_referral:', ref);

            if (ref.message === "Пользователь успешно привязан") {
                return NextResponse.redirect(new URL('/', request.url));
            } else {
                return NextResponse.redirect(new URL('/', request.url));
            }
        } catch (error) {
            console.error('Error in referral check:', error);
            return NextResponse.redirect(new URL('/error', request.url));
        }
    }
    return NextResponse.next()
}

// export default async function middlewareHandler(request: NextRequest, event: NextFetchEvent) {
//     const sslResponse = middleware(request, event);
//     if (sslResponse) return sslResponse;

//     return referralMiddleware(request);
// }