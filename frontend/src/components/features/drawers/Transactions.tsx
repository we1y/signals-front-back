'use client'

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { balanceService } from "@/services/balance.service";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/common/card";
import { useTranslations } from "next-intl";

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
            <div className='flex flex-col space-y-4 h-96 overflow-y-scroll pb-6'>
                <h1 className="text-black font-bold text-center">{t("title")}</h1>
                {data?.map((transaction) => (
                    <Card key={transaction.id}>
                        <CardHeader>
                            <CardTitle>{data ? transaction.transaction_type : 'Loading...'}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {data ? transaction.amount : 'Loading...'}
                        </CardContent>
                        <CardFooter>
                            {data ? transaction.created_at.toLocaleString() : 'Loading...'}
                        </CardFooter>
                    </Card>
                )).reverse()}
            </div>
    )
}
