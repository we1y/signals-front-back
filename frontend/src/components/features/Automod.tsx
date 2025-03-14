'use client'

import { Card } from "@/components/ui/common/card"
import { useTranslations } from "next-intl";
import { Switch } from "@/components/ui/common/switch";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { userService } from "@/services/user.service";
import { useRouter } from "next/navigation";
import { EnableAutomodResponse } from "@/types/user.interface";

export default function Automod() {
    const t = useTranslations('Automod')
    const queryClient = useQueryClient();
    const router = useRouter();

    const { data } = useQuery({
        queryKey: ['user automod'],
        queryFn: () => userService.getAutomod(),
    })

    const enable = useMutation({
        mutationKey: ['user automod'],
        mutationFn: () => userService.setAutomodEnable(),
        onError: () => {
            queryClient.invalidateQueries();
            router.push(`/failed?message=${encodeURIComponent("Неизвесатная ошибка")}`);
        },
        onSuccess: (data: EnableAutomodResponse) => {
            if (data.success == false) {
                queryClient.invalidateQueries();
                router.push(`/failed?message=${encodeURIComponent("Авто-мод не включен, недостаточно средств на балансе")}`);
            } else {
                queryClient.invalidateQueries();
            }
        }
    })

    const disable = useMutation({
        mutationKey: ['user automod'],
        mutationFn: () => userService.setAutomodDisable(),
        onError: (error: any) => console.log(error),
        onSuccess: () => {
            queryClient.invalidateQueries();
        }
    })

    const handleToggle = () => {
        if (data == true) {
            disable.mutate();
        } else {
            enable.mutate();
        }
    };

    return (
            <Card className='flex items-center justify-between p-4 bg-gradient-custom text-black rounded-full'>
                <div className="flex flex-col font-bold">
                    {t("label")}
                    <Switch className="bg-muted" checked={data} onCheckedChange={handleToggle} />
                </div>
                <Link href="/automod" className="underline">{t("info")}</Link>
            </Card>
    )
}