import {getRequestConfig} from 'next-intl/server';
import { cookies } from 'next/headers';
 
export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const locale = cookieStore.get('locale') ? cookieStore.get("locale")?.value : 'ru'
 
  return {
    locale,
    messages: (await import(`../../public/messages/${locale}.json`)).default
  };
});