'use client'

import * as React from "react"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/common/card"
import { useQuery } from "@tanstack/react-query"
import { balanceService } from "@/services/balance.service"
import { VisuallyHidden } from "@radix-ui/react-visually-hidden"
import { Button } from "@/components/ui/common/button"
import { Drawer, DrawerTrigger, DrawerContent, DrawerTitle } from "@/components/ui/common/drawer"
import TopupTrading from "@/components/features/drawers/TopupTrading"
import { useTranslations } from "next-intl"
import { Settings } from "lucide-react"
import Link from "next/link"

export default function Balance() {
    const { data, isLoading } = useQuery({
            queryKey: ['balance'],
            queryFn: () => balanceService.getUserBalance(),
        })
    const t = useTranslations('Balance')

    return (
            <Card className='text-center'>
                <CardHeader className="flex flex-row items-center justify-between text-center font-bold pt-4">
                    {t('title')}
                    <Link
                        href="/settings"
                        prefetch={false}
                    >
                        <Settings />
                    </Link>
                </CardHeader>
                <CardContent className="font-bold text-2xl">
                    {isLoading ? t('loading') : (data?.trade_balance || 0).toFixed(5)} USDT
                </CardContent>
                <CardFooter className="pb-2 px-2">
                    <Drawer>
                            <DrawerTrigger asChild>
                                <Button className='h-full w-full flex flex-col items-center font-black text-sm bg-primary-foreground hover:bg-primary-foreground'>
                                    {t('button')}
                                </Button>
                            </DrawerTrigger>
                            <DrawerContent aria-describedby={undefined} className='flex items-center'>
                                <DrawerTitle>
                                    <VisuallyHidden>{t('title')}</VisuallyHidden>
                                </DrawerTitle>
                                <TopupTrading />
                            </DrawerContent>
                        </Drawer>    
                </CardFooter>
            </Card>
    )
}
