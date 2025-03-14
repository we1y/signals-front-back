'use client'

import { useRouter, useSearchParams } from 'next/navigation';
import BackButton from "@/components/features/telegram/BackButton";
import { Button } from '@/components/ui/common/button';
import failed from '../../../public/icons/hand.png';
import Image from 'next/image';

export default function Success() {
    const searchParams = useSearchParams();
    const message = searchParams.get('message');
    const router = useRouter();

    return (
        <div className='flex items-center justify-center min-h-screen'>
            <div className='text-center m-2 items-center flex flex-col'>
                <BackButton />
                <Image src={failed} alt='Success Icon' />
                {message && <p className='font-bold m-2'>{message}</p>}
                <Button className='hover:bg-primary-foreground w-full' onClick={() => router.push('/')}>
                    Вернуться на главную
                </Button>
            </div>
        </div>
    );
}