'use client'

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { balanceService } from "@/services/balance.service";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/common/card";
import { useTranslations } from "next-intl";
import BackButton from "@/components/features/telegram/BackButton";

export default function Transactions() {
    const { data, isLoading } = useQuery({
        queryKey: ['transactions'],
        queryFn: () => balanceService.transactions()
    })

    const t = useTranslations("Transactions")

    if (isLoading) {
        return <div className="text-black">{t("loading")}</div>
    }

    return (
            <div className='flex flex-col space-y-2 font-bold m-2'>
                <BackButton />
                {data?.map((transaction) => (
                    <Card key={transaction.id} className="bg-foreground text-black">
                        <CardHeader>
                            <CardTitle>{data ? transaction.transaction_type : t("loading")}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {data ? transaction.amount : t("loading")}
                        </CardContent>
                        <CardFooter>
                            {data ? transaction.created_at.toLocaleString() : t("loading")}
                        </CardFooter>
                    </Card>
                )).reverse()}
            </div>
    )
}
