'use client'

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import failed from "../../../public/icons/hand.png"
import Image from "next/image";

export default function Desktop() {
    const t = useTranslations("Auth");
    const router = useRouter();

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className='text-center m-2 items-center flex flex-col'>
                <Image src={failed} alt=""/>
                <h1 className="font-bold m-4">{t("desktop")}</h1>
            </div>
        </div>
    )
  };