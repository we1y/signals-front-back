'use client'

import BackButton from "@/components/features/telegram/BackButton"
import { Button } from "@/components/ui/common/button"
import { Card } from "@/components/ui/common/card"
import { profitsService } from "@/services/profits.service"
import { signalService } from "@/services/signal.service"
import { userService } from "@/services/user.service"
import { JoinSignal, JoinSignalResponse } from "@/types/signal.interface"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { CodeSquare } from "lucide-react"
import { useTranslations } from "next-intl"
import { useRouter } from "next/navigation"

export default function Signals() {
    const currentTime = new Date();

    const { data, isLoading } = useQuery({
        queryKey: ['active signals'],
        queryFn: () => signalService.activeSignals() 
    })

    const queryClient = useQueryClient();
    const router = useRouter();

    // const { data: profits } = useQuery({
    //     queryKey: ['profits'],
    //     queryFn: () => profitsService.profits()
    // });

    const user = useQuery({
        queryKey: ['user telegram id'],
        queryFn: () => userService.getUser()
    })

    const t = useTranslations('Signals');

    const mutation = useMutation({
    mutationKey: ['join signal'],
    mutationFn: async ({ telegram_id, signal_id }: JoinSignal): Promise<JoinSignalResponse> => {
        const response = await signalService.joinSignal(telegram_id, signal_id);
        if (response === undefined) {
            queryClient.invalidateQueries();
            router.push(`/success?message=${encodeURIComponent("Ошибка входа в сигнал, проверьте ваш баланс")}`);
            throw new Error("Received undefined response from joinSignal");
        }
        return response;
    },
    onError: (error: Error) => {
        console.log(error.message);
    },
    onSuccess: (data: JoinSignalResponse) => {
        queryClient.invalidateQueries();
        router.push(`/success?message=${encodeURIComponent("Вы успешно вошли в сигнал")}`);
    }
    });

    if (isLoading) return <div>{t("loading")}</div>

    return (
        <div className='flex flex-col m-2 space-y-2 overflow-y-scroll font-bold'>
        <BackButton />
        {data ? data?.active_signals?.map((signal) => {
            const remainingTime = new Date(signal.expires_at).getTime() - currentTime.getTime();
            const remainingHours = Math.floor(remainingTime / (1000 * 60 * 60));
            const remainingMinutes = Math.floor((remainingTime % (1000 * 60 * 60)) / (1000 * 60));

            return (
            <Card key={signal.signal_id} className="space-y-4 p-4 text-center bg-foreground text-black rounded-2xl">
                <div className="flex justify-between items-center">
                    {t('id')}: {signal.signal_id}
                    <Button 
                    className="bg-primary text-primary-foreground hover:bg-primary"
                        onClick={() => (mutation.mutate({
                            telegram_id: user.data?.telegram_id ?? 0, 
                            signal_id: signal.signal_id
                        }))}>
                            {t('sign')}: {signal.signal_cost}$
                    </Button>
                </div>
                <div className="space-x-2 grid grid-cols-3">
                    <div className="bg-blue-200 rounded-3xl flex items-center justify-center flex-col">
                        <p>{t("risk")}:</p>
                        {(signal.burn_chance * 100).toFixed(2)}%        
                    </div>
                    <div className="bg-blue-200 rounded-3xl flex items-center justify-center flex-col">
                        <p>{t("profit")}:</p>   
                        {/* {profits}    */}
                    </div>
                    <div className="bg-blue-200 rounded-3xl flex items-center justify-center flex-col">
                        <p>{t("time")}:</p>
                        {remainingHours} {t("hours")} {remainingMinutes} {t("minutes")}       
                    </div>
                </div>
                <div className="text-start text-xs">
                    Дневная прибыль эквивалента = 1000%
                </div>
            </Card>
            )
        }) : t("noactivesignals")}
        </div>
    )
}