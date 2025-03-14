'use client'

import { Button } from "../ui/common/button";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import failed from "../../../public/icons/hand.png"
import Image from "next/image";

export default function Auth() {
    const t = useTranslations("Auth");
    const router = useRouter();

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className='text-center m-2 items-center flex flex-col'>
                <Image src={failed} alt=""/>
                <h1 className="font-bold m-4">{t("title")}</h1>
                <Button className='hover:bg-primary-foreground' onClick={() => router.push(`${process.env.NEXT_PUBLIC_BOT_URL}`)}>
                    {t("authorize")}
                </Button>
            </div>
        </div>
    )
  };