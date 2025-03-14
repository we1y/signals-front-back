'use client'

import * as React from "react";
import {
  Card,
  CardDescription,
  CardTitle,
} from "@/components/ui/common/card";
import Image from 'next/image';
import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import timer from "../../../public/icons/timer.png"
import { userService } from "@/services/user.service";

export default function Signals() {
    const { data, isLoading } = useQuery({
        queryKey: ['signals'],
        queryFn: () => userService.inWork()
    })

    const t = useTranslations('SignalsCard')

    return (
            <Card className='flex items-center justify-between p-4 bg-gradient-custom text-black rounded-full'>
                <Image src={timer} alt="" width={60} height={60}/>
                <div>
                    <CardTitle>{t("inprogress")}</CardTitle>
                    <CardDescription className="text-muted">
                        {isLoading ? t('loading') : data ? data : t('noinprogress')}
                    </CardDescription>
                </div>
                <Link href='/signals' className="[&_svg]:size-9">
                    <ArrowRight className='cursor-pointer bg-primary-foreground text-black rounded-full p-2' />
                </Link>
            </Card>
    )
}